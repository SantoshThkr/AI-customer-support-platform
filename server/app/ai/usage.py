from sqlalchemy.orm import Session

from app.models import AIOperation, AIUsage


def record_usage(
    db: Session,
    *,
    operation: AIOperation,
    model: str,
    usage=None,
    user_id: int | None = None,
    ticket_id: int | None = None,
) -> AIUsage:
    """Store token counts reported by the API. Missing counts stay null rather than guessed."""
    entry = AIUsage(
        operation=operation,
        model=model,
        user_id=user_id,
        ticket_id=ticket_id,
        input_tokens=getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "completion_tokens", None),
    )
    db.add(entry)
    return entry
