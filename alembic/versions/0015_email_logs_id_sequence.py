"""Fix email_logs.id to use a sequence (auto-increment) on existing DBs

Migration 0007 created email_logs with id INTEGER PRIMARY KEY (no SERIAL),
so inserts failed with null id. This migration attaches a sequence so
existing production DBs start recording email counts.

Revision ID: 0015_email_logs_id_seq
Revises: 0014_alert_schedule_last_enqueued_at
Create Date: 2026-02-17

"""

from alembic import op


revision = "0015_email_logs_id_seq"
down_revision = "0014_alert_schedule_last_enqueued_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Attach a sequence to email_logs.id so inserts get auto-generated ids.
    # Safe if the table was created with SERIAL (sequence already exists).
    op.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS email_logs_id_seq;
        ALTER TABLE email_logs ALTER COLUMN id SET DEFAULT nextval('email_logs_id_seq');
        SELECT setval(
            'email_logs_id_seq',
            (SELECT COALESCE(MAX(id), 0) + 1 FROM email_logs)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE email_logs ALTER COLUMN id DROP DEFAULT;
        DROP SEQUENCE IF EXISTS email_logs_id_seq;
        """
    )
