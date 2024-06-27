from pydantic import BaseModel

from app.models import TicketPriority, TicketStatus


class CategoryCount(BaseModel):
    category: str | None
    count: int


class PriorityCount(BaseModel):
    priority: TicketPriority
    count: int


class DailyCount(BaseModel):
    date: str
    count: int


class AnalyticsOut(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    average_resolution_hours: float | None
    by_status: dict[TicketStatus, int]
    by_category: list[CategoryCount]
    by_priority: list[PriorityCount]
    created_last_14_days: list[DailyCount]
