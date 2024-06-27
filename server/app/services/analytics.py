from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CLOSED_STATUSES, Ticket, TicketPriority, TicketStatus


def ticket_analytics(db: Session) -> dict:
    by_status = {ticket_status: 0 for ticket_status in TicketStatus}
    by_status.update(
        dict(db.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all())
    )
    total = sum(by_status.values())
    resolved = sum(by_status[s] for s in CLOSED_STATUSES)

    avg_seconds = db.scalar(
        select(func.avg(func.extract("epoch", Ticket.resolved_at - Ticket.created_at))).where(
            Ticket.resolved_at.is_not(None)
        )
    )

    by_category = db.execute(
        select(Ticket.category, func.count(Ticket.id))
        .group_by(Ticket.category)
        .order_by(func.count(Ticket.id).desc())
    ).all()

    priority_counts = dict(
        db.execute(select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)).all()
    )

    since = datetime.now(UTC).date() - timedelta(days=13)
    created_on = func.date(Ticket.created_at)
    daily = dict(
        db.execute(
            select(created_on, func.count(Ticket.id))
            .where(Ticket.created_at >= since)
            .group_by(created_on)
        ).all()
    )

    return {
        "total_tickets": total,
        "open_tickets": total - resolved,
        "resolved_tickets": resolved,
        "average_resolution_hours": round(float(avg_seconds) / 3600, 1) if avg_seconds else None,
        "by_status": by_status,
        "by_category": [{"category": code, "count": count} for code, count in by_category],
        "by_priority": [
            {"priority": priority, "count": priority_counts.get(priority, 0)}
            for priority in TicketPriority
        ],
        "created_last_14_days": [
            {
                "date": (since + timedelta(days=offset)).isoformat(),
                "count": daily.get(since + timedelta(days=offset), 0),
            }
            for offset in range(14)
        ],
    }
