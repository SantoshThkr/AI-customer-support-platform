from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models import User
from app.schemas.analytics import AnalyticsOut
from app.schemas.system_settings import SystemSettings, SystemSettingsUpdate
from app.services.analytics import ticket_analytics
from app.services.system_settings import get_system_settings, update_system_settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return ticket_analytics(db)


@router.get("/settings", response_model=SystemSettings)
def read_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_system_settings(db)


@router.patch("/settings", response_model=SystemSettings)
def change_settings(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return update_system_settings(db, payload.model_dump(exclude_none=True))
