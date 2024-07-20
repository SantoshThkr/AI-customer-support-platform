from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models import DocumentFileType, DocumentStatus
from app.schemas.user import UserBrief


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str | None
    file_type: DocumentFileType
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    embedded_chunk_count: int
    uploaded_by: UserBrief | None
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentOut):
    content: str


class SearchResultOut(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    section: str | None
    chunk_text: str
    score: float


class SearchResponse(BaseModel):
    mode: Literal["semantic", "keyword"]
    results: list[SearchResultOut]
