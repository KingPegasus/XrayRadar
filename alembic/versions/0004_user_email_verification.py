"""Add email_verified and verification_token to users table

Revision ID: 0004_user_email_verification
Revises: 0003_project_alert_settings
Create Date: 2026-01-27

"""

from alembic import op


revision = "0004_user_email_verification"
down_revision = "0003_project_alert_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64) NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_verification_token
            ON users(verification_token) WHERE verification_token IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_users_verification_token;
        ALTER TABLE users DROP COLUMN IF EXISTS verification_token;
        ALTER TABLE users DROP COLUMN IF EXISTS email_verified;
        """
    )
