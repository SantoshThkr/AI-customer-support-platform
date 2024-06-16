"""create categories, tickets and ticket events

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = [
    ("ACCOUNT", "Account", "Account access, profile details, team members and account settings."),
    ("BILLING", "Billing", "Invoices, charges, refunds, plan changes and payment methods."),
    ("TECHNICAL", "Technical", "Setup, configuration, integrations and how-to questions."),
    ("BUG", "Bug", "Something in the product is broken or behaves incorrectly."),
    ("FEATURE_REQUEST", "Feature request", "Requests for new functionality or improvements."),
    ("SECURITY", "Security", "Suspicious activity, compromised accounts, vulnerabilities or data privacy."),
    ("OTHER", "Other", "Anything that does not fit another category."),
]


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.bulk_insert(
        categories,
        [{"code": code, "name": name, "description": description} for code, name, description in DEFAULT_CATEGORIES],
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_agent_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), sa.ForeignKey("categories.code"), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "URGENT", name="ticket_priority"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("OPEN", "IN_PROGRESS", "WAITING_FOR_CUSTOMER", "RESOLVED", "CLOSED", name="ticket_status"),
            nullable=False,
        ),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_sentiment", sa.Enum("POSITIVE", "NEUTRAL", "NEGATIVE", name="sentiment"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(description, ''))",
                persisted=True,
            ),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])
    op.create_index("ix_tickets_assigned_agent_id", "tickets", ["assigned_agent_id"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_status_priority", "tickets", ["status", "priority"])
    op.create_index("ix_tickets_updated_at", "tickets", ["updated_at"])
    op.create_index("ix_tickets_search_vector", "tickets", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "ticket_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "TICKET_CREATED",
                "TICKET_ASSIGNED",
                "STATUS_CHANGED",
                "PRIORITY_CHANGED",
                "CATEGORY_CHANGED",
                "MESSAGE_ADDED",
                "AI_ANALYSIS_COMPLETED",
                "TICKET_RESOLVED",
                name="ticket_event_type",
            ),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])


def downgrade() -> None:
    op.drop_table("ticket_events")
    op.drop_table("tickets")
    op.drop_table("categories")
    for enum_name in ("ticket_event_type", "sentiment", "ticket_status", "ticket_priority"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
