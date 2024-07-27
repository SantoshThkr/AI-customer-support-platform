from typing import Literal

from pydantic import BaseModel, Field

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


class SourceOut(BaseModel):
    document_id: int
    document_title: str
    section: str | None


class SuggestionRequest(BaseModel):
    instructions: str | None = Field(
        default=None,
        max_length=500,
        description="Optional guidance for this draft, e.g. 'mention the refund timeline'",
    )


class SuggestionOut(BaseModel):
    suggestion: str
    sources: list[SourceOut]


class CopilotTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1_000)
    history: list[CopilotTurn] = Field(default_factory=list, max_length=10)


class CopilotOut(BaseModel):
    answer: str
    sources: list[SourceOut]
