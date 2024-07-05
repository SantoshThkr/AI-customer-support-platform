from pydantic import BaseModel

from app.models import Sentiment, TicketPriority


class AIStatus(BaseModel):
    available: bool
    reason: str | None = None


class TicketAnalysisOut(BaseModel):
    category: str
    priority: TicketPriority
    sentiment: Sentiment
    summary: str


class SummaryOut(BaseModel):
    summary: str
