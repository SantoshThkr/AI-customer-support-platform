from datetime import datetime

from pydantic import BaseModel

from app.models import AIOperation, TicketPriority, TicketStatus


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
    ai_requests_last_30_days: int


class UsageTotals(BaseModel):
    requests: int
    input_tokens: int
    output_tokens: int


class OperationUsage(UsageTotals):
    operation: AIOperation


class ModelUsage(UsageTotals):
    model: str


class UserUsage(BaseModel):
    user_id: int | None
    name: str
    requests: int


class UsageRecord(BaseModel):
    id: int
    operation: AIOperation
    model: str
    input_tokens: int | None
    output_tokens: int | None
    user_name: str | None
    ticket_id: int | None
    created_at: datetime


class AIUsageReport(BaseModel):
    days: int
    totals: UsageTotals
    # Requests where the API did not report token counts; totals exclude them.
    requests_without_token_counts: int
    by_operation: list[OperationUsage]
    by_model: list[ModelUsage]
    by_day: list[DailyCount]
    top_users: list[UserUsage]
    recent: list[UsageRecord]
