from pydantic import BaseModel


class SystemSettings(BaseModel):
    ai_enabled: bool = True
    auto_analyze_tickets: bool = True


class SystemSettingsUpdate(BaseModel):
    ai_enabled: bool | None = None
    auto_analyze_tickets: bool | None = None
