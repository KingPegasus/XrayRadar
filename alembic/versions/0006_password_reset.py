"""Add password_reset_token and password_reset_expires_at to users table

Revision ID: 0006_password_reset
Revises: 0005_deletion_requests
Create Date: 2026-01-27

"""

from alembic import op


revision = "0006_password_reset"
down_revision = "0005_deletion_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(64) NULL;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_password_reset_token
            ON users(password_reset_token) WHERE password_reset_token IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_users_password_reset_token;
        ALTER TABLE users DROP COLUMN IF EXISTS password_reset_expires_at;
        ALTER TABLE users DROP COLUMN IF EXISTS password_reset_token;
        """
    )
