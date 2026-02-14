"""User API: Pro team members, project assignment, invites."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...deps import require_pro_user, require_user
from ...email_templates import render_team_invite_email
from ...email_log import log_email
from ...db import SessionLocal
from ...models import Project, ProjectMember, ProjectMemberEnvironment, TeamInvite, User
from ...routers.user._helpers import require_owned_project
from ...schemas import (
    InviteAccept,
    InviteCreate,
    InviteOut,
    ProjectMemberAdd,
    TeamMemberOut,
)
from ...constants import (
    MAX_TEAM_MEMBERS_BY_PLAN,
    RESEND_API_KEY as DEFAULT_RESEND_API_KEY,
    RESEND_FROM_EMAIL as DEFAULT_RESEND_FROM_EMAIL,
    XRAYRADAR_BASE_URL as DEFAULT_XRAYRADAR_BASE_URL,
)

router = APIRouter()

INVITE_EXPIRY_DAYS = 7
RESEND_API_KEY = DEFAULT_RESEND_API_KEY
RESEND_FROM_EMAIL = DEFAULT_RESEND_FROM_EMAIL
XRAYRADAR_BASE_URL = DEFAULT_XRAYRADAR_BASE_URL


def _get_team_member_count(db: Session, owner_id: int) -> int:
    """Count distinct users with access to owner's projects (members) or pending invites. Excludes owner."""
    owned = select(Project.id).where(Project.owner_user_id == owner_id)
    member_ids = set(
        r[0]
        for r in db.execute(
            select(ProjectMember.user_id).where(
                ProjectMember.project_id.in_(owned),
                ProjectMember.user_id != owner_id,
            )
        ).all()
    )
    pending = db.execute(
        select(TeamInvite.email).where(
            TeamInvite.inviter_user_id == owner_id,
            TeamInvite.used_at.is_(None),
            TeamInvite.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
        )
    ).scalars().all()
    pending_emails = { (r[0] or "").strip().lower() for r in pending if (r[0] or "").strip() }
    if not pending_emails:
        return len(member_ids)
    member_emails = set()
    if member_ids:
        for row in db.execute(select(User.email).where(User.id.in_(member_ids))).scalars().all():
            if row[0]:
                member_emails.add((row[0] or "").strip().lower())
    return len(member_ids) + len(pending_emails - member_emails)


def _send_invite_email(invite_token: str, to_email: str, inviter_email: str) -> bool:
    """Legacy direct sender kept for compatibility tests."""
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        return False
    subject, html = render_team_invite_email(
        base_url=XRAYRADAR_BASE_URL,
        invite_token=invite_token,
        inviter_email=inviter_email,
    )
    try:
        import resend

        resend.api_key = RESEND_API_KEY
        resend.Emails.send(
            params={
                "from": RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )
        return True
    except Exception:  # noqa: BLE001
        return False


def _send_invite_and_log(invite_token: str, to_email: str, inviter_email: str, inviter_user_id: int) -> None:
    sent = _send_invite_email(invite_token, to_email, inviter_email)
    db = SessionLocal()
    try:
        log_email(db, "team_invite", to_email, success=sent, user_id=inviter_user_id)
    finally:
        db.close()


@router.get("/api/user/team/members", response_model=list[TeamMemberOut])
def team_list_members(
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """List users who have access to at least one of the current user's projects (team members)."""
    # Projects owned by current user
    owned = select(Project.id).where(Project.owner_user_id == user.id)
    # All project_members rows for those projects
    members_q = (
        select(ProjectMember.user_id, ProjectMember.project_id)
        .where(ProjectMember.project_id.in_(owned))
    )
    rows = db.execute(members_q).all()
    # Aggregate by user_id: { user_id: [project_id, ...] }
    by_user: dict[int, list[int]] = {}
    for r in rows:
        uid, pid = r[0], r[1]
        by_user.setdefault(uid, []).append(pid)
    if not by_user:
        return []
    users_q = select(User).where(User.id.in_(by_user.keys()))
    users = {u.id: u for u in db.execute(users_q).scalars().all()}
    return [
        TeamMemberOut(
            user_id=uid,
            email=users[uid].email,
            project_ids=sorted(project_ids),
        )
        for uid, project_ids in by_user.items()
        if uid in users
    ]


@router.post("/api/user/projects/{project_id}/members", response_model=TeamMemberOut)
def project_add_member(
    project_id: int,
    payload: ProjectMemberAdd,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """Assign a user to a project (Pro owner only). Provide user_id or email."""
    project = require_owned_project(db, user=user, project_id=project_id)
    if payload.user_id is not None and payload.email is not None:
        raise HTTPException(status_code=400, detail="Provide user_id or email, not both")
    if payload.user_id is None and not (payload.email or "").strip():
        raise HTTPException(status_code=400, detail="Provide user_id or email")

    if payload.user_id is not None:
        member_user = db.get(User, payload.user_id)
        if member_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        member_user = db.execute(
            select(User).where(User.email == (payload.email or "").strip().lower())
        ).scalars().first()
        if member_user is None:
            raise HTTPException(status_code=404, detail="User not found")

    if member_user.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a member")

    existing = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_user.id,
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="User already has access to this project")

    max_members = MAX_TEAM_MEMBERS_BY_PLAN.get(user.plan, 0)
    current_count = _get_team_member_count(db, user.id)
    owned = select(Project.id).where(Project.owner_user_id == user.id)
    already_member = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id.in_(owned),
            ProjectMember.user_id == member_user.id,
        )
    ).first() is not None
    if not already_member and current_count >= max_members:
        raise HTTPException(
            status_code=400,
            detail=f"Team member limit reached ({max_members} for your plan). Upgrade to add more.",
        )

    db.add(ProjectMember(project_id=project_id, user_id=member_user.id))
    db.commit()

    # Return this user's team membership (all projects they have access to from this owner)
    owned = select(Project.id).where(Project.owner_user_id == user.id)
    members_q = (
        select(ProjectMember.project_id)
        .where(ProjectMember.user_id == member_user.id)
        .where(ProjectMember.project_id.in_(owned))
    )
    pids = [r[0] for r in db.execute(members_q).all()]
    return TeamMemberOut(
        user_id=member_user.id,
        email=member_user.email,
        project_ids=sorted(pids),
    )


@router.delete("/api/user/projects/{project_id}/members/{member_user_id}", status_code=204)
def project_revoke_member(
    project_id: int,
    member_user_id: int,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """Revoke a user's access to a project (Pro owner only)."""
    require_owned_project(db, user=user, project_id=project_id)
    pm = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_user_id,
        )
    ).scalars().first()
    if pm is not None:
        db.delete(pm)
        db.commit()


@router.delete("/api/user/team/members/{member_user_id}", status_code=204)
def team_remove_member(
    member_user_id: int,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """Remove a user from all of the current user's projects (Pro owner only)."""
    owned = select(Project.id).where(Project.owner_user_id == user.id)
    to_delete = db.execute(
        select(ProjectMember).where(
            ProjectMember.user_id == member_user_id,
            ProjectMember.project_id.in_(owned),
        )
    ).scalars().all()
    for pm in to_delete:
        db.delete(pm)
    db.commit()


@router.get("/api/user/projects/{project_id}/members/{member_user_id}/environments", response_model=list[str])
def project_member_list_environments(
    project_id: int,
    member_user_id: int,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    rows = (
        db.execute(
            select(ProjectMemberEnvironment.environment).where(
                ProjectMemberEnvironment.project_id == project_id,
                ProjectMemberEnvironment.user_id == member_user_id,
            )
        )
        .scalars()
        .all()
    )
    return [r for r in rows if r]


@router.put("/api/user/projects/{project_id}/members/{member_user_id}/environments", response_model=dict)
def project_member_replace_environments(
    project_id: int,
    member_user_id: int,
    payload: dict,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    member = (
        db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == member_user_id,
            )
        )
        .scalars()
        .first()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    envs = payload.get("environments") if isinstance(payload, dict) else None
    envs = envs if isinstance(envs, list) else []
    normalized: list[str] = []
    seen: set[str] = set()
    for e in envs:
        if not isinstance(e, str):
            continue
        s = e.strip()
        if s and s not in seen:
            seen.add(s)
            normalized.append(s)
    existing = (
        db.execute(
            select(ProjectMemberEnvironment).where(
                ProjectMemberEnvironment.project_id == project_id,
                ProjectMemberEnvironment.user_id == member_user_id,
            )
        )
        .scalars()
        .all()
    )
    for row in existing:
        db.delete(row)
    for env in normalized:
        db.add(
            ProjectMemberEnvironment(
                project_id=project_id,
                user_id=member_user_id,
                environment=env,
            )
        )
    db.commit()
    return {"ok": True, "environments": normalized}


@router.post("/api/user/team/invites", response_model=InviteOut)
def team_create_invite(
    payload: InviteCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """Create a team invite and send email (Pro owner only). project_ids must be owned by current user."""
    if not payload.project_ids:
        raise HTTPException(status_code=400, detail="At least one project_id required")
    for pid in payload.project_ids:
        proj = db.get(Project, pid)
        if proj is None or proj.owner_user_id != user.id:
            raise HTTPException(status_code=404, detail=f"Project {pid} not found or not owned by you")
    email = (payload.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    max_members = MAX_TEAM_MEMBERS_BY_PLAN.get(user.plan, 0)
    current_count = _get_team_member_count(db, user.id)
    if current_count >= max_members:
        raise HTTPException(
            status_code=400,
            detail=f"Team member limit reached ({max_members} for your plan). Upgrade to add more.",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=INVITE_EXPIRY_DAYS)
    invite = TeamInvite(
        inviter_user_id=user.id,
        email=email,
        token=token,
        expires_at=expires_at,
        project_ids=payload.project_ids,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    # Async delivery to keep invite creation responsive.
    background_tasks.add_task(_send_invite_and_log, token, email, user.email, user.id)

    return InviteOut(
        id=invite.id,
        email=invite.email,
        project_ids=invite.project_ids or [],
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


@router.get("/api/user/team/invites", response_model=list[InviteOut])
def team_list_invites(
    user: User = Depends(require_pro_user),
    db: Session = Depends(get_db),
):
    """List pending invites sent by the current user (Pro only)."""
    q = (
        select(TeamInvite)
        .where(TeamInvite.inviter_user_id == user.id)
        .where(TeamInvite.used_at.is_(None))
        .where(TeamInvite.expires_at > datetime.now(timezone.utc).replace(tzinfo=None))
        .order_by(TeamInvite.created_at.desc())
    )
    rows = db.execute(q).scalars().all()
    return [
        InviteOut(
            id=inv.id,
            email=inv.email,
            project_ids=inv.project_ids or [],
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in rows
    ]


@router.post("/api/user/team/invites/accept", status_code=204)
def team_accept_invite(
    payload: InviteAccept,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Accept a team invite. Caller must be logged in; invite email must match current user."""
    token = (payload.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token required")
    invite = db.execute(
        select(TeamInvite).where(TeamInvite.token == token)
    ).scalars().first()
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.used_at is not None:
        raise HTTPException(status_code=400, detail="Invite already used")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if invite.expires_at < now:
        raise HTTPException(status_code=400, detail="Invite expired")
    if (invite.email or "").strip().lower() != (user.email or "").strip().lower():
        raise HTTPException(status_code=403, detail="Invite was sent to a different email address")

    project_ids = invite.project_ids or []
    for pid in project_ids:
        proj = db.get(Project, pid)
        if proj is None:
            continue
        if proj.owner_user_id != invite.inviter_user_id:
            continue
        existing = db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == pid,
                ProjectMember.user_id == user.id,
            )
        ).scalars().first()
        if existing is None:
            db.add(ProjectMember(project_id=pid, user_id=user.id))
    invite.used_at = now
    db.add(invite)
    db.commit()
