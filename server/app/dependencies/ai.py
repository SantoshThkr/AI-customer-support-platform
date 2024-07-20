from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.client import ensure_ai_available
from app.config import settings
from app.database import get_db
from app.dependencies.auth import require_staff
from app.models import User
from app.services.rate_limit import RateLimiter

ai_rate_limiter = RateLimiter(limit=settings.ai_requests_per_minute, window_seconds=60)


def ai_request_user(db: Session = Depends(get_db), user: User = Depends(require_staff)) -> User:
    """Staff user making an AI request, after availability and rate-limit checks."""
    ensure_ai_available(db)
    if not ai_rate_limiter.allow(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many AI requests. Please wait a minute and try again.",
        )
    return user
