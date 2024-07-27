from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import AIServiceError, chat_completion
from app.ai.usage import record_usage
from app.models import AIOperation, Ticket, TicketMessage, User
from app.services.knowledge import SearchResult, search_knowledge

MAX_SOURCES = 4
# Semantic matches below this cosine similarity are usually unrelated articles.
MIN_SIMILARITY = 0.2
OTHER_TICKETS_LIMIT = 5


@dataclass
class PreparedPrompt:
    messages: list[dict]
    sources: list[SearchResult]


def load_conversation(db: Session, ticket: Ticket) -> list[TicketMessage]:
    return list(
        db.scalars(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.created_at, TicketMessage.id)
        ).all()
    )


def find_sources(db: Session, query: str, ticket: Ticket, user: User) -> list[SearchResult]:
    mode, results = search_knowledge(db, query, MAX_SOURCES, user_id=user.id, ticket_id=ticket.id)
    if mode == "semantic":
        results = [result for result in results if result.score >= MIN_SIMILARITY]
    return results


def _latest_customer_text(ticket: Ticket, conversation: list[TicketMessage]) -> str:
    for message in reversed(conversation):
        if message.sender_id == ticket.customer_id:
            return message.message
    return ticket.description


def prepare_suggestion(
    db: Session, ticket: Ticket, user: User, instructions: str | None = None
) -> PreparedPrompt:
    conversation = load_conversation(db, ticket)
    query = f"{ticket.subject}\n{_latest_customer_text(ticket, conversation)}"
    sources = find_sources(db, query[:2_000], ticket, user)
    return PreparedPrompt(
        messages=prompts.suggestion_messages(ticket, conversation, sources, user, instructions),
        sources=sources,
    )


def prepare_copilot(
    db: Session, ticket: Ticket, user: User, question: str, history: list[dict]
) -> PreparedPrompt:
    """Context for the copilot: this ticket, this customer's other tickets and matching articles."""
    conversation = load_conversation(db, ticket)
    other_tickets = list(
        db.scalars(
            select(Ticket)
            .where(Ticket.customer_id == ticket.customer_id, Ticket.id != ticket.id)
            .order_by(Ticket.created_at.desc())
            .limit(OTHER_TICKETS_LIMIT)
        ).all()
    )
    sources = find_sources(db, f"{question}\n{ticket.subject}"[:2_000], ticket, user)
    return PreparedPrompt(
        messages=prompts.copilot_messages(
            ticket, conversation, sources, other_tickets, history, question
        ),
        sources=sources,
    )


def complete(
    db: Session, prepared: PreparedPrompt, operation: AIOperation, ticket: Ticket, user: User
) -> str:
    response = chat_completion(prepared.messages, max_tokens=700, temperature=0.4)
    record_usage(
        db,
        operation=operation,
        model=response.model,
        usage=response.usage,
        user_id=user.id,
        ticket_id=ticket.id,
    )
    db.commit()

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise AIServiceError("The AI service returned an empty response")
    return text
