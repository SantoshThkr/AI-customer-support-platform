from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import ensure_ai_available
from app.database import get_db
from app.dependencies.ai import ai_rate_limiter
from app.dependencies.auth import require_admin, require_staff
from app.models import DocumentFileType, DocumentStatus, KnowledgeDocument, User
from app.schemas.knowledge import DocumentDetail, DocumentOut, SearchResponse, SearchResultOut
from app.services import knowledge as knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _get_document(db: Session, document_id: int) -> KnowledgeDocument:
    document = db.get(KnowledgeDocument, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(default=None),
    title: str | None = Form(default=None, max_length=200),
    content: str | None = Form(default=None, max_length=200_000),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Upload a .txt/.md/.pdf file, or send `title` + `content` to write an article directly."""
    if file is not None and file.filename:
        file_type, text = knowledge_service.read_upload(file.file, file.filename)
        filename = file.filename[:255]
        title = title or knowledge_service.default_title(file.filename, text)
    elif content and title:
        file_type = DocumentFileType.MARKDOWN
        text = knowledge_service.clean_text(content)
        filename = None
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a file, or provide both a title and content",
        )

    document = knowledge_service.create_document(
        db, title=title, text=text, file_type=file_type, filename=filename, uploaded_by=user
    )
    if document.status == DocumentStatus.PROCESSING:
        background_tasks.add_task(knowledge_service.embed_document, document.id)
    return document


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.title)).all()


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return _get_document(db, document_id)


@router.post("/documents/{document_id}/embed", response_model=DocumentOut)
def regenerate_embeddings(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Retry embedding a document, e.g. after a failure or after AI was switched on."""
    document = _get_document(db, document_id)
    ensure_ai_available(db)
    document.status = DocumentStatus.PROCESSING
    document.error_message = None
    db.commit()
    background_tasks.add_task(knowledge_service.embed_document, document.id)
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    db.delete(_get_document(db, document_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/search", response_model=SearchResponse)
def search_knowledge(
    q: str = Query(min_length=2, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
):
    # Semantic search costs an embedding call, so it counts towards the AI rate
    # limit; once the limit is hit, agents still get keyword results.
    mode, results = knowledge_service.search_knowledge(
        db, q, limit, use_ai=ai_rate_limiter.allow(user.id), user_id=user.id
    )
    return SearchResponse(
        mode=mode,
        results=[
            SearchResultOut(
                chunk_id=result.chunk.id,
                document_id=result.chunk.document_id,
                document_title=result.chunk.document.title,
                section=result.chunk.metadata_.get("section"),
                chunk_text=result.chunk.chunk_text,
                score=round(result.score, 4),
            )
            for result in results
        ],
    )
