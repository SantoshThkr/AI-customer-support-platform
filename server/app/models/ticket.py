import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin
from app.models.user import User


class TicketPriority(str, enum.Enum):
    # Declaration order matters: PostgreSQL sorts enum values in this order.
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CUSTOMER = "WAITING_FOR_CUSTOMER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


CLOSED_STATUSES = (TicketStatus.RESOLVED, TicketStatus.CLOSED)


class Sentiment(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class TicketEventType(str, enum.Enum):
    TICKET_CREATED = "TICKET_CREATED"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    CATEGORY_CHANGED = "CATEGORY_CHANGED"
    MESSAGE_ADDED = "MESSAGE_ADDED"
    AI_ANALYSIS_COMPLETED = "AI_ANALYSIS_COMPLETED"
    TICKET_RESOLVED = "TICKET_RESOLVED"


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(ForeignKey("categories.code"), index=True)
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"), default=TicketPriority.MEDIUM
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"), default=TicketStatus.OPEN
    )
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_sentiment: Mapped[Sentiment | None] = mapped_column(Enum(Sentiment, name="sentiment"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(description, ''))",
            persisted=True,
        ),
        deferred=True,
    )

    customer: Mapped[User] = relationship(foreign_keys=[customer_id], lazy="joined")
    assigned_agent: Mapped[User | None] = relationship(
        foreign_keys=[assigned_agent_id], lazy="joined"
    )


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    event_type: Mapped[TicketEventType] = mapped_column(
        Enum(TicketEventType, name="ticket_event_type")
    )
    # "metadata" is reserved on declarative models, hence the attribute name.
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(lazy="joined")
