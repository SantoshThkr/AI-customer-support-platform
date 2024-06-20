from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBrief


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    is_internal: bool = False


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    sender: UserBrief
    message: str
    is_internal: bool
    created_at: datetime


class AssignRequest(BaseModel):
    agent_id: int | None = Field(description="Agent to assign, or null to unassign")
