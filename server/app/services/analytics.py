from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CLOSED_STATUSES, AIUsage, Ticket, TicketPriority, TicketStatus, User


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

    ai_requests = db.scalar(
        select(func.count(AIUsage.id)).where(
            AIUsage.created_at >= datetime.now(UTC) - timedelta(days=30)
        )
    )

    return {
        "ai_requests_last_30_days": ai_requests,
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


def _token_sums():
    return (
        func.count(AIUsage.id),
        func.coalesce(func.sum(AIUsage.input_tokens), 0),
        func.coalesce(func.sum(AIUsage.output_tokens), 0),
    )


def ai_usage_report(db: Session, days: int) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    in_period = AIUsage.created_at >= since

    requests, input_tokens, output_tokens = db.execute(
        select(*_token_sums()).where(in_period)
    ).one()
    missing = db.scalar(
        select(func.count(AIUsage.id)).where(in_period, AIUsage.input_tokens.is_(None))
    )

    by_operation = db.execute(
        select(AIUsage.operation, *_token_sums())
        .where(in_period)
        .group_by(AIUsage.operation)
        .order_by(func.count(AIUsage.id).desc())
    ).all()
    by_model = db.execute(
        select(AIUsage.model, *_token_sums())
        .where(in_period)
        .group_by(AIUsage.model)
        .order_by(func.count(AIUsage.id).desc())
    ).all()

    start_day = since.date() + timedelta(days=1)
    used_on = func.date(AIUsage.created_at)
    daily = dict(
        db.execute(select(used_on, func.count(AIUsage.id)).where(in_period).group_by(used_on)).all()
    )

    top_users = db.execute(
        select(AIUsage.user_id, User.name, func.count(AIUsage.id))
        .outerjoin(User, User.id == AIUsage.user_id)
        .where(in_period)
        .group_by(AIUsage.user_id, User.name)
        .order_by(func.count(AIUsage.id).desc())
        .limit(5)
    ).all()

    recent = db.execute(
        select(AIUsage, User.name)
        .outerjoin(User, User.id == AIUsage.user_id)
        .order_by(AIUsage.created_at.desc(), AIUsage.id.desc())
        .limit(20)
    ).all()

    return {
        "days": days,
        "totals": {
            "requests": requests,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "requests_without_token_counts": missing,
        "by_operation": [
            {"operation": op, "requests": n, "input_tokens": i, "output_tokens": o}
            for op, n, i, o in by_operation
        ],
        "by_model": [
            {"model": model, "requests": n, "input_tokens": i, "output_tokens": o}
            for model, n, i, o in by_model
        ],
        "by_day": [
            {
                "date": (start_day + timedelta(days=offset)).isoformat(),
                "count": daily.get(start_day + timedelta(days=offset), 0),
            }
            for offset in range(days)
        ],
        "top_users": [
            {"user_id": user_id, "name": name or "Automatic (system)", "requests": n}
            for user_id, name, n in top_users
        ],
        "recent": [
            {
                "id": usage.id,
                "operation": usage.operation,
                "model": usage.model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "user_name": name,
                "ticket_id": usage.ticket_id,
                "created_at": usage.created_at,
            }
            for usage, name in recent
        ],
    }
