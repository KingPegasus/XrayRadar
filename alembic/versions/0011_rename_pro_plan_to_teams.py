"""Rename Pro plan to Teams

Revision ID: 0011_rename_pro_plan_to_teams
Revises: 0010_project_members_team_invites
Create Date: 2026-02-06

"""

from alembic import op


revision = "0011_rename_pro_plan_to_teams"
down_revision = "0010_project_members_team_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET plan = 'Teams' WHERE plan = 'Pro'")


def downgrade() -> None:
    op.execute("UPDATE users SET plan = 'Pro' WHERE plan = 'Teams'")
