from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Sentiment, TicketEventType, TicketPriority, TicketStatus
from app.schemas.user import UserBrief


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10_000)


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: str | None = Field(default=None, max_length=50)


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    description: str
    category: str | None
    priority: TicketPriority
    status: TicketStatus
    ai_summary: str | None
    ai_sentiment: Sentiment | None
    customer: UserBrief
    assigned_agent: UserBrief | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class TicketEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: TicketEventType
    user: UserBrief | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    created_at: datetime
