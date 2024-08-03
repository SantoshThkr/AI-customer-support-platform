from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.ai import response_suggestions, ticket_analysis
from app.ai.client import AIUnavailableError, ensure_ai_available
from app.database import get_db
from app.dependencies.ai import ai_request_user
from app.dependencies.auth import require_staff
from app.dependencies.tickets import get_accessible_ticket
from app.models import AIOperation, Ticket, User
from app.schemas.ai import (
    AIStatus,
    CopilotOut,
    CopilotRequest,
    SourceOut,
    SuggestionOut,
    SuggestionRequest,
    SummaryOut,
    TicketAnalysisOut,
)
from app.services.knowledge import SearchResult

router = APIRouter(prefix="/api/ai", tags=["ai"])

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def source_list(results: list[SearchResult]) -> list[SourceOut]:
    return [
        SourceOut(
            document_id=result.chunk.document_id,
            document_title=result.chunk.document.title,
            section=result.chunk.metadata_.get("section"),
        )
        for result in results
    ]


@router.get("/status", response_model=AIStatus)
def get_ai_status(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    try:
        ensure_ai_available(db)
    except AIUnavailableError as exc:
        return AIStatus(available=False, reason=str(exc))
    return AIStatus(available=True)


@router.post("/tickets/{ticket_id}/analyze", response_model=TicketAnalysisOut)
def analyze_ticket(
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    return ticket_analysis.analyze_ticket(db, ticket, user)


@router.post("/tickets/{ticket_id}/summarize", response_model=SummaryOut)
def summarize_ticket(
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    return SummaryOut(summary=ticket_analysis.summarize_ticket(db, ticket, user))


@router.post("/tickets/{ticket_id}/suggest-response", response_model=SuggestionOut)
def suggest_response(
    payload: SuggestionRequest | None = None,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    """Draft a reply for the agent to review. Nothing is sent to the customer."""
    instructions = payload.instructions if payload else None
    prepared = response_suggestions.prepare_suggestion(db, ticket, user, instructions)
    suggestion = response_suggestions.complete(
        db, prepared, AIOperation.SUGGESTED_RESPONSE, ticket, user
    )
    return SuggestionOut(suggestion=suggestion, sources=source_list(prepared.sources))


@router.post("/tickets/{ticket_id}/copilot", response_model=CopilotOut)
def ask_copilot(
    payload: CopilotRequest,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    history = [turn.model_dump() for turn in payload.history]
    prepared = response_suggestions.prepare_copilot(db, ticket, user, payload.question, history)
    answer = response_suggestions.complete(db, prepared, AIOperation.COPILOT, ticket, user)
    return CopilotOut(answer=answer, sources=source_list(prepared.sources))


@router.post("/tickets/{ticket_id}/suggest-response/stream")
def stream_suggested_response(
    payload: SuggestionRequest | None = None,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    """Same as suggest-response, streamed as Server-Sent Events:
    `sources`, then `delta` events with text, then `done` (or `error`)."""
    instructions = payload.instructions if payload else None
    prepared = response_suggestions.prepare_suggestion(db, ticket, user, instructions)
    events = response_suggestions.stream_completion(
        prepared,
        operation=AIOperation.SUGGESTED_RESPONSE,
        ticket_id=ticket.id,
        user_id=user.id,
        sources=[source.model_dump() for source in source_list(prepared.sources)],
    )
    return StreamingResponse(events, media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/tickets/{ticket_id}/copilot/stream")
def stream_copilot(
    payload: CopilotRequest,
    ticket: Ticket = Depends(get_accessible_ticket),
    db: Session = Depends(get_db),
    user: User = Depends(ai_request_user),
):
    history = [turn.model_dump() for turn in payload.history]
    prepared = response_suggestions.prepare_copilot(db, ticket, user, payload.question, history)
    events = response_suggestions.stream_completion(
        prepared,
        operation=AIOperation.COPILOT,
        ticket_id=ticket.id,
        user_id=user.id,
        sources=[source.model_dump() for source in source_list(prepared.sources)],
    )
    return StreamingResponse(events, media_type="text/event-stream", headers=SSE_HEADERS)
