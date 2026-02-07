"""Add email_logs table for tracking sent emails

Revision ID: 0007_email_log
Revises: 0006_password_reset
Create Date: 2026-02-02

"""

from alembic import op


revision = "0007_email_log"
down_revision = "0006_password_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY,
            email_type VARCHAR(32) NOT NULL,
            recipient_email VARCHAR(320) NOT NULL,
            sent_at TIMESTAMP NOT NULL,
            project_id INTEGER NULL,
            user_id INTEGER NULL,
            success BOOLEAN NOT NULL DEFAULT true,
            error_message TEXT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS ix_email_logs_email_type ON email_logs(email_type);
        CREATE INDEX IF NOT EXISTS ix_email_logs_sent_at ON email_logs(sent_at);
        CREATE INDEX IF NOT EXISTS ix_email_logs_project_id ON email_logs(project_id);
        CREATE INDEX IF NOT EXISTS ix_email_logs_user_id ON email_logs(user_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_email_logs_user_id;
        DROP INDEX IF EXISTS ix_email_logs_project_id;
        DROP INDEX IF EXISTS ix_email_logs_sent_at;
        DROP INDEX IF EXISTS ix_email_logs_email_type;
        DROP TABLE IF EXISTS email_logs;
        """
    )
