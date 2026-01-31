"""Project alert settings, recipients, and cooldown (idempotent)

Revision ID: 0003_project_alert_settings
Revises: 0002_user_projects_fingerprints
Create Date: 2026-01-27

"""

from alembic import op


revision = "0003_project_alert_settings"
down_revision = "0002_user_projects_fingerprints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_alert_settings (
            project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            level_filter VARCHAR(32) NOT NULL DEFAULT 'error',
            cooldown_minutes INTEGER NULL
        );

        CREATE TABLE IF NOT EXISTS project_alert_recipients (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            email VARCHAR(320) NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_project_alert_recipients_project_email
            ON project_alert_recipients(project_id, email);
        CREATE INDEX IF NOT EXISTS ix_project_alert_recipients_project_id
            ON project_alert_recipients(project_id);

        CREATE TABLE IF NOT EXISTS alert_cooldown (
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            fingerprint VARCHAR(64) NOT NULL,
            last_notified_at TIMESTAMP NOT NULL,
            PRIMARY KEY (project_id, fingerprint)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS alert_cooldown;
        DROP TABLE IF EXISTS project_alert_recipients;
        DROP TABLE IF EXISTS project_alert_settings;
        """
    )
