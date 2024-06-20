from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin, require_roles, require_staff
from app.dependencies.tickets import get_accessible_ticket
from app.models import (
    Ticket,
    TicketEvent,
    TicketEventType,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)
from app.schemas.common import Page
from app.schemas.message import AssignRequest, MessageCreate, MessageOut
from app.schemas.ticket import TicketCreate, TicketEventOut, TicketOut, TicketUpdate
from app.services import tickets as ticket_service
from app.services.tickets import TicketFilters

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def serialize_ticket(ticket: Ticket, user: User) -> TicketOut:
    data = TicketOut.model_validate(ticket)
    if not user.is_staff:
        # AI triage output (sentiment, internal summary) is meant for the support team only.
        data = data.model_copy(update={"ai_summary": None, "ai_sentiment": None})
    return data


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    ticket = ticket_service.create_ticket(db, user, payload)
    return serialize_ticket(ticket, user)


@router.get("", response_model=Page[TicketOut])
def list_tickets(
    search: str | None = Query(default=None, max_length=200),
    status_filter: list[TicketStatus] = Query(default=[], alias="status"),
    priority: list[TicketPriority] = Query(default=[]),
    category: str | None = Query(default=None, max_length=50),
    assigned_agent: str | None = Query(default=None, pattern=r"^(me|unassigned|\d+)$"),
    customer_id: int | None = None,
    sort: Literal["created_at", "updated_at", "priority", "status"] = "updated_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = TicketFilters(
        search=search,
        statuses=status_filter,
        priorities=priority,
        category=category,
        assigned_agent=assigned_agent,
        customer_id=customer_id,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    tickets, total = ticket_service.list_tickets(db, user, filters)
    return Page.build([serialize_ticket(t, user) for t in tickets], total, page, page_size)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket: Ticket = Depends(get_accessible_ticket),
    user: User = Depends(get_current_user),
):
    return serialize_ticket(ticket, user)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    payload: TicketUpdate,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    changes = payload.model_dump(exclude_none=True)

    if not user.is_staff:
        if set(changes) != {"status"} or changes["status"] != TicketStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only close their own tickets",
            )
    else:
        ticket_service.ensure_can_work_on(user, ticket)

    if "category" in changes:
        ticket_service.change_category(db, ticket, user, changes["category"])
    if "priority" in changes:
        ticket_service.change_priority(db, ticket, user, changes["priority"])
    if "status" in changes:
        ticket_service.change_status(db, ticket, user, changes["status"])

    db.commit()
    db.refresh(ticket)
    return serialize_ticket(ticket, user)


@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
def list_messages(
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ticket_service.list_messages(db, ticket, user)


@router.post(
    "/{ticket_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED
)
def add_message(
    payload: MessageCreate,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ticket_service.add_message(db, ticket, user, payload.message, payload.is_internal)


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    payload: AssignRequest,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
):
    ticket = ticket_service.assign_ticket(db, ticket, user, payload.agent_id)
    return serialize_ticket(ticket, user)


def visible_to_customer(event: TicketEvent) -> bool:
    if event.event_type == TicketEventType.AI_ANALYSIS_COMPLETED:
        return False
    return not event.metadata_.get("is_internal", False)


@router.get("/{ticket_id}/events", response_model=list[TicketEventOut])
def list_ticket_events(
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    events = db.scalars(
        select(TicketEvent)
        .where(TicketEvent.ticket_id == ticket.id)
        .order_by(TicketEvent.created_at, TicketEvent.id)
    ).all()
    if not user.is_staff:
        events = [event for event in events if visible_to_customer(event)]
    return events


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
