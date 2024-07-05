from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SystemSetting
from app.schemas.system_settings import SystemSettings


def get_system_settings(db: Session) -> SystemSettings:
    stored = dict(db.execute(select(SystemSetting.key, SystemSetting.value)).all())
    known = {key: value for key, value in stored.items() if key in SystemSettings.model_fields}
    return SystemSettings(**known)


def update_system_settings(db: Session, changes: dict) -> SystemSettings:
    for key, value in changes.items():
        db.merge(SystemSetting(key=key, value=value))
    db.commit()
    return get_system_settings(db)
