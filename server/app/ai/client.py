import logging
from functools import lru_cache

import openai
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.knowledge import EMBEDDING_DIMENSIONS
from app.services.system_settings import get_system_settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Base class for AI failures. These must never break the core ticket workflow."""


class AIUnavailableError(AIError):
    """AI is not configured on this server or has been turned off by an admin."""


class AIServiceError(AIError):
    """OpenAI failed, timed out, or returned something we could not use."""


def ai_is_configured() -> bool:
    return bool(settings.openai_api_key)


def ensure_ai_available(db: Session) -> None:
    if not ai_is_configured():
        raise AIUnavailableError("AI features are not configured on this server")
    if not get_system_settings(db).ai_enabled:
        raise AIUnavailableError("AI features have been turned off by an administrator")


def ai_available(db: Session) -> bool:
    try:
        ensure_ai_available(db)
    except AIUnavailableError:
        return False
    return True


@lru_cache
def _build_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, timeout=settings.openai_timeout_seconds, max_retries=1)


def get_client() -> OpenAI:
    if not ai_is_configured():
        raise AIUnavailableError("AI features are not configured on this server")
    return _build_client(settings.openai_api_key)


def _provider_error(exc: openai.OpenAIError) -> AIServiceError:
    if isinstance(exc, openai.APITimeoutError):
        logger.warning("OpenAI request timed out")
        return AIServiceError("The AI service timed out. Please try again.")
    # Log the error type and status only; provider messages can echo request details.
    logger.warning(
        "OpenAI request failed: %s (status=%s)",
        exc.__class__.__name__,
        getattr(exc, "status_code", None),
    )
    return AIServiceError("The AI service is having problems. Please try again later.")


def chat_completion(
    messages: list[dict],
    *,
    json_schema: dict | None = None,
    max_tokens: int = 500,
    temperature: float = 0.2,
):
    client = get_client()
    params = {
        "model": settings.openai_chat_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_schema:
        params["response_format"] = {"type": "json_schema", "json_schema": json_schema}

    try:
        return client.chat.completions.create(**params)
    except openai.OpenAIError as exc:
        raise _provider_error(exc) from exc


def create_embeddings(texts: list[str]):
    client = get_client()
    try:
        return client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
        )
    except openai.OpenAIError as exc:
        raise _provider_error(exc) from exc
