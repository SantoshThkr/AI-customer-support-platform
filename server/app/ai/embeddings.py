from sqlalchemy.orm import Session

from app.ai.client import AIServiceError, create_embeddings
from app.ai.usage import record_usage
from app.models import AIOperation
from app.models.knowledge import EMBEDDING_DIMENSIONS

BATCH_SIZE = 64


def embed_texts(
    db: Session,
    texts: list[str],
    *,
    user_id: int | None = None,
    ticket_id: int | None = None,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = create_embeddings(batch)
        # Embedding responses only report input tokens; output tokens stay null.
        record_usage(
            db,
            operation=AIOperation.EMBEDDING,
            model=response.model,
            usage=response.usage,
            user_id=user_id,
            ticket_id=ticket_id,
        )
        db.commit()

        items = sorted(response.data, key=lambda item: item.index)
        if len(items) != len(batch) or any(
            len(item.embedding) != EMBEDDING_DIMENSIONS for item in items
        ):
            raise AIServiceError("The AI service returned unexpected embeddings")
        vectors.extend(item.embedding for item in items)
    return vectors


def embed_query(
    db: Session, text: str, *, user_id: int | None = None, ticket_id: int | None = None
) -> list[float]:
    return embed_texts(db, [text], user_id=user_id, ticket_id=ticket_id)[0]
