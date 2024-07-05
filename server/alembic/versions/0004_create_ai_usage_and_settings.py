"""create ai usage and system settings

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "operation",
            sa.Enum(
                "CLASSIFICATION",
                "SUMMARY",
                "SUGGESTED_RESPONSE",
                "COPILOT",
                "EMBEDDING",
                name="ai_operation",
            ),
            nullable=False,
        ),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_usage_user_id", "ai_usage", ["user_id"])
    op.create_index("ix_ai_usage_ticket_id", "ai_usage", ["ticket_id"])
    op.create_index("ix_ai_usage_created_at", "ai_usage", ["created_at"])

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("ai_usage")
    sa.Enum(name="ai_operation").drop(op.get_bind(), checkfirst=True)
