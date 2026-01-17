"""Initial schema (idempotent)

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-17

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(320) NULL,
            token VARCHAR(255) NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS uq_tokens_token ON tokens(token);
        CREATE INDEX IF NOT EXISTS ix_tokens_email ON tokens(email);
        CREATE INDEX IF NOT EXISTS ix_tokens_token ON tokens(token);

        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            timestamp TIMESTAMP NOT NULL,
            level VARCHAR(32) NOT NULL,
            message VARCHAR(2048) NOT NULL,
            environment VARCHAR(64) NULL,
            release VARCHAR(64) NULL,
            server_name VARCHAR(255) NULL,
            payload JSONB NOT NULL
        );

        CREATE INDEX IF NOT EXISTS ix_events_project_id ON events(project_id);
        CREATE INDEX IF NOT EXISTS ix_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS ix_events_level ON events(level);
        CREATE INDEX IF NOT EXISTS ix_events_environment ON events(environment);
        CREATE INDEX IF NOT EXISTS ix_events_release ON events(release);

        CREATE TABLE IF NOT EXISTS token_project_access (
            id SERIAL PRIMARY KEY,
            token_id INTEGER NOT NULL REFERENCES tokens(id),
            project_id INTEGER NOT NULL REFERENCES projects(id),
            created_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP NULL
        );

        CREATE INDEX IF NOT EXISTS ix_token_project_access_token_id ON token_project_access(token_id);
        CREATE INDEX IF NOT EXISTS ix_token_project_access_project_id ON token_project_access(project_id);

        ALTER TABLE tokens
        ADD COLUMN IF NOT EXISTS email VARCHAR(320);

        CREATE INDEX IF NOT EXISTS ix_tokens_email ON tokens(email);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS token_project_access;
        DROP TABLE IF EXISTS events;
        DROP TABLE IF EXISTS tokens;
        DROP TABLE IF EXISTS projects;
        """
    )
