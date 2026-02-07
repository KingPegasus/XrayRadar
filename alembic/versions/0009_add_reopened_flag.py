"""Add reopened flag to issue_status table

Revision ID: 0009_add_reopened_flag
Revises: 0008_issue_status
Create Date: 2026-02-02

"""

from alembic import op


revision = "0009_add_reopened_flag"
down_revision = "0008_issue_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE issue_status ADD COLUMN reopened BOOLEAN NOT NULL DEFAULT false;
        CREATE INDEX IF NOT EXISTS ix_issue_status_reopened ON issue_status(reopened);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_issue_status_reopened;
        ALTER TABLE issue_status DROP COLUMN reopened;
        """
    )
