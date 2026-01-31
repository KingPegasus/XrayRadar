"""Add deletion_requests table for account deletion workflow

Revision ID: 0005_deletion_requests
Revises: 0004_user_email_verification
Create Date: 2026-01-27

"""

from alembic import op


revision = "0005_deletion_requests"
down_revision = "0004_user_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS deletion_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reason TEXT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            fulfilled_at TIMESTAMP NULL,
            cancelled_at TIMESTAMP NULL
        );
        CREATE INDEX IF NOT EXISTS ix_deletion_requests_user_id ON deletion_requests(user_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS deletion_requests;
        """
    )
