"""User projects + token requests + event fingerprints (idempotent)

Revision ID: 0002_user_projects_fingerprints
Revises: 0001_init
Create Date: 2026-01-24
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0002_user_projects_fingerprints"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- Users table (model exists; ensure DB has it for migration-driven deploys)
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(320) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            plan VARCHAR(32) NOT NULL DEFAULT 'Free',
            created_at TIMESTAMP NOT NULL,
            last_login_at TIMESTAMP NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

        -- Project ownership (user_id is nullable for existing rows)
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS owner_user_id INTEGER NULL REFERENCES users(id);
        CREATE INDEX IF NOT EXISTS ix_projects_owner_user_id ON projects(owner_user_id);

        -- Tokens can optionally be associated with a user
        ALTER TABLE tokens
        ADD COLUMN IF NOT EXISTS user_id INTEGER NULL REFERENCES users(id);
        CREATE INDEX IF NOT EXISTS ix_tokens_user_id ON tokens(user_id);

        -- Event fingerprint used for grouping
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(64) NULL;
        CREATE INDEX IF NOT EXISTS ix_events_fingerprint ON events(fingerprint);

        -- Token requests (user -> admin fulfillment)
        CREATE TABLE IF NOT EXISTS token_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR(200) NOT NULL,
            note TEXT NULL,
            created_at TIMESTAMP NOT NULL,
            fulfilled_at TIMESTAMP NULL,
            fulfilled_token_id INTEGER NULL REFERENCES tokens(id)
        );
        CREATE INDEX IF NOT EXISTS ix_token_requests_user_id ON token_requests(user_id);
        CREATE INDEX IF NOT EXISTS ix_token_requests_fulfilled_token_id ON token_requests(fulfilled_token_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS token_requests;
        -- Columns dropped only on downgrade (best-effort)
        ALTER TABLE events DROP COLUMN IF EXISTS fingerprint;
        ALTER TABLE tokens DROP COLUMN IF EXISTS user_id;
        ALTER TABLE projects DROP COLUMN IF EXISTS owner_user_id;
        DROP TABLE IF EXISTS users;
        """
    )

