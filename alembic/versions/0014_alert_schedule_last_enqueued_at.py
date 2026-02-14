"""Add last_enqueued_at to alert_schedule_state for ingest/scheduler dedupe

Revision ID: 0014_alert_schedule_last_enqueued_at
Revises: 0013_alert_scheduler_state
Create Date: 2026-02-15

"""

from alembic import op
import sqlalchemy as sa


revision = "0014_alert_schedule_last_enqueued_at"
down_revision = "0013_alert_scheduler_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alert_schedule_state",
        sa.Column("last_enqueued_at", sa.DateTime(timezone=False), nullable=True),
    )
    op.create_index(
        "ix_alert_schedule_state_last_enqueued_at",
        "alert_schedule_state",
        ["last_enqueued_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_alert_schedule_state_last_enqueued_at",
        table_name="alert_schedule_state",
    )
    op.drop_column("alert_schedule_state", "last_enqueued_at")
