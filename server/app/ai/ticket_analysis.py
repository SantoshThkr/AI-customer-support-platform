import logging

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import AIError, AIServiceError, ai_is_configured, chat_completion
from app.ai.usage import record_usage
from app.database import SessionLocal
from app.models import (
    AIOperation,
    Category,
    Sentiment,
    Ticket,
    TicketEventType,
    TicketMessage,
    TicketPriority,
    User,
)
from app.services.system_settings import get_system_settings
from app.services.tickets import record_event

logger = logging.getLogger(__name__)

MAX_SUMMARY_CHARS = 1_000


class TicketAnalysis(BaseModel):
    category: str
    priority: TicketPriority
    sentiment: Sentiment
    summary: str = Field(min_length=1, max_length=MAX_SUMMARY_CHARS)

    @field_validator("category", "priority", "sentiment", mode="before")
    @classmethod
    def normalise_codes(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("summary")
    @classmethod
    def strip_summary(cls, value: str) -> str:
        return value.strip()


def parse_analysis(content: str | None, allowed_categories: set[str]) -> TicketAnalysis:
    if not content:
        raise AIServiceError("The AI service returned an empty analysis")
    try:
        analysis = TicketAnalysis.model_validate_json(content)
    except ValidationError as exc:
        logger.warning("Discarding invalid ticket analysis: %s", exc.errors()[:3])
        raise AIServiceError("The AI service returned an invalid analysis") from exc
    if analysis.category not in allowed_categories:
        logger.warning("Discarding ticket analysis with unknown category %r", analysis.category)
        raise AIServiceError("The AI service returned an unknown category")
    return analysis


def analyze_ticket(db: Session, ticket: Ticket, user: User | None) -> TicketAnalysis:
    categories = db.scalars(select(Category).where(Category.is_active.is_(True))).all()
    codes = [category.code for category in categories]

    response = chat_completion(
        prompts.analysis_messages(ticket, list(categories)),
        json_schema=prompts.analysis_schema(codes),
        max_tokens=300,
        temperature=0,
    )
    # Tokens are spent whether or not the output turns out to be usable.
    record_usage(
        db,
        operation=AIOperation.CLASSIFICATION,
        model=response.model,
        usage=response.usage,
        user_id=user.id if user else None,
        ticket_id=ticket.id,
    )
    db.commit()

    analysis = parse_analysis(response.choices[0].message.content, set(codes))

    previous_priority = ticket.priority
    ticket.category = analysis.category
    ticket.priority = analysis.priority
    ticket.ai_sentiment = analysis.sentiment
    ticket.ai_summary = analysis.summary
    record_event(
        db,
        ticket,
        user,
        TicketEventType.AI_ANALYSIS_COMPLETED,
        category=analysis.category,
        priority=analysis.priority.value,
        previous_priority=previous_priority.value,
        sentiment=analysis.sentiment.value,
    )
    db.commit()
    db.refresh(ticket)
    return analysis


def summarize_ticket(db: Session, ticket: Ticket, user: User) -> str:
    messages = db.scalars(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket.id)
        .order_by(TicketMessage.created_at, TicketMessage.id)
    ).all()

    response = chat_completion(
        prompts.summary_messages(ticket, list(messages)), max_tokens=250, temperature=0.2
    )
    record_usage(
        db,
        operation=AIOperation.SUMMARY,
        model=response.model,
        usage=response.usage,
        user_id=user.id,
        ticket_id=ticket.id,
    )
    db.commit()

    summary = (response.choices[0].message.content or "").strip()
    if not summary:
        raise AIServiceError("The AI service returned an empty summary")

    ticket.ai_summary = summary[:MAX_SUMMARY_CHARS]
    db.commit()
    return ticket.ai_summary


def analyze_new_ticket(ticket_id: int) -> None:
    """Background task run after a ticket is created. Failures are logged, never raised."""
    if not ai_is_configured():
        return

    with SessionLocal() as db:
        system_settings = get_system_settings(db)
        if not (system_settings.ai_enabled and system_settings.auto_analyze_tickets):
            return
        ticket = db.get(Ticket, ticket_id)
        if ticket is None:
            return
        try:
            analyze_ticket(db, ticket, user=None)
        except AIError as exc:
            logger.warning("Automatic analysis failed for ticket %s: %s", ticket_id, exc)
        except Exception:
            logger.exception("Unexpected error while analysing ticket %s", ticket_id)
