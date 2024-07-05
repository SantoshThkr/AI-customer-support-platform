import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIOperation(str, enum.Enum):
    CLASSIFICATION = "CLASSIFICATION"
    SUMMARY = "SUMMARY"
    SUGGESTED_RESPONSE = "SUGGESTED_RESPONSE"
    COPILOT = "COPILOT"
    EMBEDDING = "EMBEDDING"


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Null for work the system starts on its own, e.g. analysing a new ticket.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="SET NULL"), index=True
    )
    operation: Mapped[AIOperation] = mapped_column(Enum(AIOperation, name="ai_operation"))
    model: Mapped[str] = mapped_column(String(100))
    # Null when the API response did not report token counts.
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
