from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models import User
from app.schemas.analytics import AnalyticsOut
from app.services.analytics import ticket_analytics

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return ticket_analytics(db)
