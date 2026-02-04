"""Add issue_status table for tracking issue lifecycle

Revision ID: 0008_issue_status
Revises: 0007_email_log
Create Date: 2026-02-02

"""

from alembic import op


revision = "0008_issue_status"
down_revision = "0007_email_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS issue_status (
            project_id INTEGER NOT NULL,
            fingerprint VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'open',
            resolved_release VARCHAR(64) NULL,
            resolved_at TIMESTAMP NULL,
            resolved_by_user_id INTEGER NULL,
            notes TEXT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (project_id, fingerprint),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (resolved_by_user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS ix_issue_status_status ON issue_status(status);
        CREATE INDEX IF NOT EXISTS ix_issue_status_resolved_release ON issue_status(resolved_release);
        CREATE INDEX IF NOT EXISTS ix_issue_status_updated_at ON issue_status(updated_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_issue_status_updated_at;
        DROP INDEX IF EXISTS ix_issue_status_resolved_release;
        DROP INDEX IF EXISTS ix_issue_status_status;
        DROP TABLE IF EXISTS issue_status;
        """
    )
