"""Add environment ACL, env alert settings, and email jobs

Revision ID: 0012_env_acl_alert_env_and_email_jobs
Revises: 0011_rename_pro_plan_to_teams
Create Date: 2026-02-14

"""

from alembic import op
import sqlalchemy as sa


revision = "0012_env_acl_alert_env_and_email_jobs"
down_revision = "0011_rename_pro_plan_to_teams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_member_environments",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id", "environment"),
    )

    op.create_table(
        "token_project_environment_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=False), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["token_id"], ["tokens.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_id", "project_id", "environment", name="uq_token_project_environment_access_unique"),
    )
    op.create_index(
        "ix_token_project_environment_access_token_id",
        "token_project_environment_access",
        ["token_id"],
    )
    op.create_index(
        "ix_token_project_environment_access_project_id",
        "token_project_environment_access",
        ["project_id"],
    )
    op.create_index(
        "ix_token_project_environment_access_environment",
        "token_project_environment_access",
        ["environment"],
    )

    op.create_table(
        "project_alert_environment_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "environment",
            name="uq_project_alert_environment_settings_project_environment",
        ),
    )
    op.create_index(
        "ix_project_alert_environment_settings_project_id",
        "project_alert_environment_settings",
        ["project_id"],
    )
    op.create_index(
        "ix_project_alert_environment_settings_environment",
        "project_alert_environment_settings",
        ["environment"],
    )

    op.create_table(
        "project_alert_environment_recipients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "environment",
            "email",
            name="uq_project_alert_environment_recipients_unique",
        ),
    )
    op.create_index(
        "ix_project_alert_environment_recipients_project_id",
        "project_alert_environment_recipients",
        ["project_id"],
    )
    op.create_index(
        "ix_project_alert_environment_recipients_environment",
        "project_alert_environment_recipients",
        ["environment"],
    )

    op.create_table(
        "email_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_jobs_job_type", "email_jobs", ["job_type"])
    op.create_index("ix_email_jobs_status", "email_jobs", ["status"])
    op.create_index("ix_email_jobs_next_attempt_at", "email_jobs", ["next_attempt_at"])
    op.create_index("ix_email_jobs_created_at", "email_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_email_jobs_created_at", table_name="email_jobs")
    op.drop_index("ix_email_jobs_next_attempt_at", table_name="email_jobs")
    op.drop_index("ix_email_jobs_status", table_name="email_jobs")
    op.drop_index("ix_email_jobs_job_type", table_name="email_jobs")
    op.drop_table("email_jobs")

    op.drop_index(
        "ix_project_alert_environment_recipients_environment",
        table_name="project_alert_environment_recipients",
    )
    op.drop_index(
        "ix_project_alert_environment_recipients_project_id",
        table_name="project_alert_environment_recipients",
    )
    op.drop_table("project_alert_environment_recipients")

    op.drop_index(
        "ix_project_alert_environment_settings_environment",
        table_name="project_alert_environment_settings",
    )
    op.drop_index(
        "ix_project_alert_environment_settings_project_id",
        table_name="project_alert_environment_settings",
    )
    op.drop_table("project_alert_environment_settings")

    op.drop_index(
        "ix_token_project_environment_access_environment",
        table_name="token_project_environment_access",
    )
    op.drop_index(
        "ix_token_project_environment_access_project_id",
        table_name="token_project_environment_access",
    )
    op.drop_index(
        "ix_token_project_environment_access_token_id",
        table_name="token_project_environment_access",
    )
    op.drop_table("token_project_environment_access")
    op.drop_table("project_member_environments")

