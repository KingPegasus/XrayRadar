"""Add alert scheduler state table

Revision ID: 0013_alert_scheduler_state
Revises: 0012_env_acl_alert_env_and_email_jobs
Create Date: 2026-02-15

"""

from alembic import op
import sqlalchemy as sa


revision = "0013_alert_scheduler_state"
down_revision = "0012_env_acl_alert_env_and_email_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_schedule_state",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_event_seen_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_job_key", sa.String(length=160), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "environment"),
    )
    op.create_index(
        "ix_alert_schedule_state_last_evaluated_at",
        "alert_schedule_state",
        ["last_evaluated_at"],
    )
    op.create_index(
        "ix_alert_schedule_state_last_sent_at",
        "alert_schedule_state",
        ["last_sent_at"],
    )
    op.create_index(
        "ix_alert_schedule_state_last_job_key",
        "alert_schedule_state",
        ["last_job_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_alert_schedule_state_last_job_key", table_name="alert_schedule_state")
    op.drop_index("ix_alert_schedule_state_last_sent_at", table_name="alert_schedule_state")
    op.drop_index("ix_alert_schedule_state_last_evaluated_at", table_name="alert_schedule_state")
    op.drop_table("alert_schedule_state")

