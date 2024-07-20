from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import ticket_analysis
from app.ai.client import AIUnavailableError, ensure_ai_available
from app.database import get_db
from app.dependencies.ai import ai_request_user
from app.dependencies.auth import require_staff
from app.dependencies.tickets import get_accessible_ticket
from app.models import Ticket, User
from app.schemas.ai import AIStatus, SummaryOut, TicketAnalysisOut

router = APIRouter(prefix="/api/ai", tags=["ai"])


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
