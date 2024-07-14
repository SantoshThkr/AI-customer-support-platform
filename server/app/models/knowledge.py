import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.database import Base, TimestampMixin
from app.models.user import User


class DocumentFileType(str, enum.Enum):
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"
    PDF = "PDF"


class DocumentStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[str | None] = mapped_column(String(255))
    file_type: Mapped[DocumentFileType] = mapped_column(
        Enum(DocumentFileType, name="document_file_type")
    )
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.PROCESSING
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    uploaded_by: Mapped[User | None] = relationship(lazy="joined")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="KnowledgeChunk.chunk_index",
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_index"),
        Index("ix_knowledge_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', chunk_text)", persisted=True), deferred=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


KnowledgeDocument.chunk_count = column_property(
    select(func.count(KnowledgeChunk.id))
    .where(KnowledgeChunk.document_id == KnowledgeDocument.id)
    .correlate_except(KnowledgeChunk)
    .scalar_subquery()
)
