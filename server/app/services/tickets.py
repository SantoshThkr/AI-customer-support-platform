from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    CLOSED_STATUSES,
    STAFF_ROLES,
    Category,
    Ticket,
    TicketAssignment,
    TicketEvent,
    TicketEventType,
    TicketMessage,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)
from app.schemas.ticket import TicketCreate

SORT_COLUMNS = {
    "created_at": Ticket.created_at,
    "updated_at": Ticket.updated_at,
    "priority": Ticket.priority,
    "status": Ticket.status,
}


@dataclass
class TicketFilters:
    search: str | None = None
    statuses: list[TicketStatus] = field(default_factory=list)
    priorities: list[TicketPriority] = field(default_factory=list)
    category: str | None = None
    # "me", "unassigned" or an agent id
    assigned_agent: str | None = None
    customer_id: int | None = None
    sort: str = "updated_at"
    order: str = "desc"
    page: int = 1
    page_size: int = 20


def like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _filter_conditions(user: User, filters: TicketFilters) -> list:
    conditions = []

    if user.role == UserRole.CUSTOMER:
        conditions.append(Ticket.customer_id == user.id)
    elif filters.customer_id is not None:
        conditions.append(Ticket.customer_id == filters.customer_id)

    if filters.statuses:
        conditions.append(Ticket.status.in_(filters.statuses))
    if filters.priorities:
        conditions.append(Ticket.priority.in_(filters.priorities))
    if filters.category:
        conditions.append(Ticket.category == filters.category)

    if filters.assigned_agent == "me":
        conditions.append(Ticket.assigned_agent_id == user.id)
    elif filters.assigned_agent == "unassigned":
        conditions.append(Ticket.assigned_agent_id.is_(None))
    elif filters.assigned_agent:
        conditions.append(Ticket.assigned_agent_id == int(filters.assigned_agent))

    term = (filters.search or "").strip()
    if term:
        pattern = like_pattern(term)
        matches = [
            Ticket.search_vector.op("@@")(func.websearch_to_tsquery("english", term)),
            Ticket.subject.ilike(pattern, escape="\\"),
        ]
        if term.lstrip("#").isdigit():
            matches.append(Ticket.id == int(term.lstrip("#")))
        if user.is_staff:
            matches.append(
                Ticket.customer.has(
                    or_(
                        User.email.ilike(pattern, escape="\\"),
                        User.name.ilike(pattern, escape="\\"),
                    )
                )
            )
        conditions.append(or_(*matches))

    return conditions


def list_tickets(db: Session, user: User, filters: TicketFilters) -> tuple[list[Ticket], int]:
    conditions = _filter_conditions(user, filters)
    total = db.scalar(select(func.count(Ticket.id)).where(*conditions))

    sort_column = SORT_COLUMNS.get(filters.sort, Ticket.updated_at)
    ordering = sort_column.asc() if filters.order == "asc" else sort_column.desc()
    tickets = db.scalars(
        select(Ticket)
        .where(*conditions)
        .order_by(ordering, Ticket.id.desc())
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).all()
    return list(tickets), total


def ticket_stats(db: Session, user: User) -> dict:
    scope = []
    if not user.is_staff:
        scope.append(Ticket.customer_id == user.id)

    rows = db.execute(
        select(Ticket.status, func.count(Ticket.id)).where(*scope).group_by(Ticket.status)
    ).all()
    stats = {"by_status": {ticket_status: 0 for ticket_status in TicketStatus}}
    stats["by_status"].update(dict(rows))

    if user.is_staff:
        unresolved = Ticket.status.not_in(CLOSED_STATUSES)

        def count(*conditions) -> int:
            return db.scalar(select(func.count(Ticket.id)).where(unresolved, *conditions))

        stats["assigned_to_me"] = count(Ticket.assigned_agent_id == user.id)
        stats["unassigned"] = count(Ticket.assigned_agent_id.is_(None))
        stats["urgent"] = count(Ticket.priority == TicketPriority.URGENT)
    return stats


def record_event(
    db: Session,
    ticket: Ticket,
    user: User | None,
    event_type: TicketEventType,
    **metadata,
) -> TicketEvent:
    event = TicketEvent(
        ticket_id=ticket.id,
        user_id=user.id if user else None,
        event_type=event_type,
        metadata_=metadata,
    )
    db.add(event)
    return event


def create_ticket(db: Session, customer: User, data: TicketCreate) -> Ticket:
    ticket = Ticket(
        customer_id=customer.id,
        subject=data.subject.strip(),
        description=data.description.strip(),
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    db.flush()
    record_event(db, ticket, customer, TicketEventType.TICKET_CREATED)
    db.commit()
    db.refresh(ticket)
    return ticket


def can_work_on(user: User, ticket: Ticket) -> bool:
    """Admins can work on anything; agents on unassigned tickets or their own."""
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.AGENT:
        return ticket.assigned_agent_id in (None, user.id)
    return ticket.customer_id == user.id


def ensure_can_work_on(user: User, ticket: Ticket) -> None:
    if not can_work_on(user, ticket):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ticket is assigned to another agent",
        )


def change_status(db: Session, ticket: Ticket, user: User | None, new_status: TicketStatus) -> None:
    if ticket.status == new_status:
        return

    old_status = ticket.status
    ticket.status = new_status
    if new_status in CLOSED_STATUSES:
        if ticket.resolved_at is None:
            ticket.resolved_at = datetime.now(UTC)
    else:
        ticket.resolved_at = None

    record_event(
        db,
        ticket,
        user,
        TicketEventType.STATUS_CHANGED,
        **{"from": old_status.value, "to": new_status.value},
    )
    if new_status == TicketStatus.RESOLVED:
        record_event(db, ticket, user, TicketEventType.TICKET_RESOLVED)


def change_priority(db: Session, ticket: Ticket, user: User, priority: TicketPriority) -> None:
    if ticket.priority == priority:
        return
    record_event(
        db,
        ticket,
        user,
        TicketEventType.PRIORITY_CHANGED,
        **{"from": ticket.priority.value, "to": priority.value},
    )
    ticket.priority = priority


def change_category(db: Session, ticket: Ticket, user: User, category_code: str) -> None:
    if ticket.category == category_code:
        return
    category = db.scalar(
        select(Category).where(Category.code == category_code, Category.is_active.is_(True))
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    record_event(
        db,
        ticket,
        user,
        TicketEventType.CATEGORY_CHANGED,
        **{"from": ticket.category, "to": category_code},
    )
    ticket.category = category_code


def list_messages(db: Session, ticket: Ticket, user: User) -> list[TicketMessage]:
    query = select(TicketMessage).where(TicketMessage.ticket_id == ticket.id)
    if not user.is_staff:
        query = query.where(TicketMessage.is_internal.is_(False))
    return list(db.scalars(query.order_by(TicketMessage.created_at, TicketMessage.id)).all())


def add_message(
    db: Session, ticket: Ticket, user: User, text: str, is_internal: bool = False
) -> TicketMessage:
    if is_internal and not user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support staff can add internal notes",
        )
    if not user.is_staff and ticket.status == TicketStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ticket is closed. Please open a new ticket.",
        )
    # Any agent can leave an internal note; replying to the customer is limited
    # to whoever is working on the ticket.
    if user.is_staff and not is_internal:
        ensure_can_work_on(user, ticket)

    message = TicketMessage(
        ticket_id=ticket.id, sender_id=user.id, message=text.strip(), is_internal=is_internal
    )
    db.add(message)
    db.flush()

    record_event(
        db,
        ticket,
        user,
        TicketEventType.MESSAGE_ADDED,
        message_id=message.id,
        is_internal=is_internal,
    )

    if not user.is_staff and ticket.status in (
        TicketStatus.WAITING_FOR_CUSTOMER,
        TicketStatus.RESOLVED,
    ):
        reopened = TicketStatus.IN_PROGRESS if ticket.assigned_agent_id else TicketStatus.OPEN
        change_status(db, ticket, user, reopened)

    ticket.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(message)
    return message


def assign_ticket(db: Session, ticket: Ticket, user: User, agent_id: int | None) -> Ticket:
    ensure_can_work_on(user, ticket)
    if ticket.assigned_agent_id == agent_id:
        return ticket

    agent = None
    if agent_id is not None:
        agent = db.get(User, agent_id)
        if agent is None or agent.role not in STAFF_ROLES or not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tickets can only be assigned to active support agents",
            )

    previous_agent_id = ticket.assigned_agent_id
    ticket.assigned_agent_id = agent_id
    if agent is not None:
        db.add(TicketAssignment(ticket_id=ticket.id, agent_id=agent.id, assigned_by_id=user.id))

    record_event(
        db,
        ticket,
        user,
        TicketEventType.TICKET_ASSIGNED,
        agent_id=agent_id,
        agent_name=agent.name if agent else None,
        previous_agent_id=previous_agent_id,
    )
    db.commit()
    db.refresh(ticket)
    return ticket
