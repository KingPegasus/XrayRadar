"""Add project_members and team_invites for Pro team access

Revision ID: 0010_project_members_team_invites
Revises: 0009_add_reopened_flag
Create Date: 2026-02-06

"""

from alembic import op


revision = "0010_project_members_team_invites"
down_revision = "0009_add_reopened_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Widen alembic_version.version_num so long revision IDs (e.g. this one) fit (default is 32)
    op.execute(
        "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_members (
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (project_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS ix_project_members_project_id ON project_members(project_id);
        CREATE INDEX IF NOT EXISTS ix_project_members_user_id ON project_members(user_id);

        CREATE TABLE IF NOT EXISTS team_invites (
            id SERIAL PRIMARY KEY,
            inviter_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(320) NOT NULL,
            token VARCHAR(64) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_team_invites_token ON team_invites(token);
        CREATE INDEX IF NOT EXISTS ix_team_invites_inviter_user_id ON team_invites(inviter_user_id);
        CREATE INDEX IF NOT EXISTS ix_team_invites_email ON team_invites(email);
        CREATE INDEX IF NOT EXISTS ix_team_invites_expires_at ON team_invites(expires_at);
        """
    )
    # project_ids: store JSON array; use TEXT for SQLite/Postgres compatibility
    op.execute(
        """
        ALTER TABLE team_invites ADD COLUMN IF NOT EXISTS project_ids TEXT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE team_invites DROP COLUMN IF EXISTS project_ids;
        DROP INDEX IF EXISTS ix_team_invites_expires_at;
        DROP INDEX IF EXISTS ix_team_invites_email;
        DROP INDEX IF EXISTS ix_team_invites_inviter_user_id;
        DROP INDEX IF EXISTS uq_team_invites_token;
        DROP TABLE IF EXISTS team_invites;
        DROP INDEX IF EXISTS ix_project_members_user_id;
        DROP INDEX IF EXISTS ix_project_members_project_id;
        DROP TABLE IF EXISTS project_members;
        """
    )
