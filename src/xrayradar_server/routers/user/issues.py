"""User API: issues and events."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import Event, IssueStatus, User
from ...deps import require_user
from ...schemas import BulkIssueStatusUpdate, IssueStatusOut, IssueStatusUpdate, IssueSummaryOut
from ._helpers import require_owned_project

router = APIRouter()


def _ensure_issue_status(db: Session, project_id: int, fingerprint: str) -> IssueStatus:
    """Create default 'open' status if none exists. Returns IssueStatus object."""
    issue_status = db.get(IssueStatus, (project_id, fingerprint))
    if issue_status is None:
        issue_status = IssueStatus(
            project_id=project_id,
            fingerprint=fingerprint,
            status="open",
            reopened=False,
        )
        db.add(issue_status)
        db.commit()
        db.refresh(issue_status)
    return issue_status


@router.get("/api/user/projects/{project_id}/issues", response_model=list[IssueSummaryOut])
def user_list_issues(
    project_id: int,
    limit: int = 50,
    status: str | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    clamped_limit = min(max(limit, 1), 200)
    
    # Build base aggregation query
    agg = (
        select(
            Event.fingerprint,
            func.count(Event.id).label("count"),
            func.min(Event.timestamp).label("first_seen"),
            func.max(Event.timestamp).label("last_seen"),
        )
        .where(Event.project_id == project_id)
        .where(Event.fingerprint.is_not(None))
        .group_by(Event.fingerprint)
        .order_by(func.max(Event.timestamp).desc())
        .limit(clamped_limit)
    )
    
    groups = db.execute(agg).all()
    out: list[IssueSummaryOut] = []
    
    for fp, count, first_seen, last_seen in groups:
        # Get latest event for this fingerprint
        q_latest = (
            select(Event)
            .where(Event.project_id == project_id)
            .where(Event.fingerprint == fp)
            .order_by(Event.timestamp.desc())
            .limit(1)
        )
        latest = db.execute(q_latest).scalars().first()
        if latest is None:
            continue
        
        # Get issue status
        issue_status = db.get(IssueStatus, (project_id, fp))
        
        # Filter by status if requested
        if status is not None:
            current_status = issue_status.status if issue_status else "open"
            if current_status != status:
                continue
        
        out.append(
            IssueSummaryOut(
                fingerprint=str(fp),
                count=int(count or 0),
                first_seen=first_seen,
                last_seen=last_seen,
                level=latest.level,
                message=latest.message,
                environment=latest.environment,
                release=latest.release,
                status=issue_status.status if issue_status else "open",
                resolved_release=issue_status.resolved_release if issue_status else None,
                resolved_at=issue_status.resolved_at if issue_status else None,
                reopened=issue_status.reopened if issue_status else False,
            )
        )
    return out


@router.get("/api/user/projects/{project_id}/events", response_model=list[dict])
def user_list_project_events(
    project_id: int,
    limit: int = 200,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    clamped_limit = min(max(limit, 1), 500)
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .where(Event.timestamp >= thirty_days_ago)
        .order_by(Event.timestamp.desc())
        .limit(clamped_limit)
    )
    rows = db.execute(q).scalars().all()
    return [{"id": str(r.id), "timestamp": r.timestamp, "level": r.level, "message": r.message} for r in rows]


def _date_str(date_obj) -> str:
    if isinstance(date_obj, datetime):
        return date_obj.date().isoformat()
    if hasattr(date_obj, "isoformat"):
        return date_obj.isoformat()
    s = str(date_obj)
    if " " in s or "T" in s:
        s = s.split()[0].split("T")[0]
    return s


@router.get("/api/user/projects/{project_id}/events/frequency", response_model=dict)
def user_get_project_event_frequency(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    q = (
        select(func.date(Event.timestamp).label("date"), func.count(Event.id).label("count"))
        .where(Event.project_id == project_id)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(func.date(Event.timestamp))
        .order_by(func.date(Event.timestamp))
    )
    rows = db.execute(q).all()
    frequency = {_date_str(d): int(c or 0) for d, c in rows}
    total_q = select(func.count(Event.id)).where(Event.project_id == project_id).where(Event.timestamp >= thirty_days_ago)
    total_count = db.execute(total_q).scalar() or 0
    return {"frequency": frequency, "total": total_count}


@router.get("/api/user/projects/{project_id}/issues/{fingerprint}/events/frequency", response_model=dict)
def user_get_issue_event_frequency(
    project_id: int,
    fingerprint: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    q = (
        select(func.date(Event.timestamp).label("date"), func.count(Event.id).label("count"))
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(func.date(Event.timestamp))
        .order_by(func.date(Event.timestamp))
    )
    rows = db.execute(q).all()
    frequency = {_date_str(d): int(c or 0) for d, c in rows}
    total_q = (
        select(func.count(Event.id))
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
    )
    total_count = db.execute(total_q).scalar() or 0
    return {"frequency": frequency, "total": total_count}


@router.get("/api/user/projects/{project_id}/issues/{fingerprint}/breakdown", response_model=dict)
def user_get_issue_breakdown(
    project_id: int,
    fingerprint: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Return event counts by release and by environment for this issue (last 30 days)."""
    require_owned_project(db, user=user, project_id=project_id)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # By release
    q_release = (
        select(Event.release, func.count(Event.id).label("count"))
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(Event.release)
        .order_by(func.count(Event.id).desc())
    )
    rows_release = db.execute(q_release).all()
    by_release = [{"release": r, "count": int(c or 0)} for r, c in rows_release]

    # By environment
    q_env = (
        select(Event.environment, func.count(Event.id).label("count"))
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(Event.environment)
        .order_by(func.count(Event.id).desc())
    )
    rows_env = db.execute(q_env).all()
    by_environment = [{"environment": e, "count": int(c or 0)} for e, c in rows_env]

    return {"by_release": by_release, "by_environment": by_environment}


@router.get("/api/user/projects/{project_id}/issues/{fingerprint}/events", response_model=list[dict])
def user_list_issue_events(
    project_id: int,
    fingerprint: str,
    limit: int = 50,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    clamped_limit = min(max(limit, 1), 200)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .order_by(Event.timestamp.desc())
        .limit(clamped_limit)
    )
    rows = db.execute(q).scalars().all()
    return [
        {"id": str(r.id), "timestamp": r.timestamp, "level": r.level, "message": r.message, "environment": r.environment, "release": r.release}
        for r in rows
    ]


@router.get("/api/user/projects/{project_id}/events/{event_id}", response_model=dict)
def user_get_event(
    project_id: int,
    event_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    row = db.get(Event, event_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(row.id),
        "project_id": row.project_id,
        "timestamp": row.timestamp,
        "level": row.level,
        "message": row.message,
        "environment": row.environment,
        "release": row.release,
        "server_name": row.server_name,
        "fingerprint": row.fingerprint,
        "payload": row.payload,
    }


@router.patch("/api/user/projects/{project_id}/issues/{fingerprint}/status", response_model=IssueStatusOut)
def user_update_issue_status(
    project_id: int,
    fingerprint: str,
    payload: IssueStatusUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update or create issue status."""
    require_owned_project(db, user=user, project_id=project_id)
    
    if payload.status not in ("open", "in_progress", "resolved", "ignored"):
        raise HTTPException(status_code=400, detail="Invalid status")
    
    issue_status = db.get(IssueStatus, (project_id, fingerprint))
    prev_status = None
    if issue_status is None:
        issue_status = IssueStatus(
            project_id=project_id,
            fingerprint=fingerprint,
            status=payload.status,
            reopened=False,
        )
        db.add(issue_status)
    else:
        prev_status = issue_status.status
        issue_status.status = payload.status
    
    # Handle resolved status
    if payload.status == "resolved":
        issue_status.resolved_release = payload.resolved_release
        issue_status.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        issue_status.resolved_by_user_id = user.id
        issue_status.reopened = False  # Clear reopened flag when resolving
    else:
        # Clear resolution fields if not resolved
        issue_status.resolved_release = None
        issue_status.resolved_at = None
        issue_status.resolved_by_user_id = None
        # If manually changing from resolved to open, mark as reopened
        if prev_status == "resolved" and payload.status == "open":
            issue_status.reopened = True
    
    # Update notes if provided
    if payload.notes is not None:
        issue_status.notes = payload.notes
    
    db.commit()
    db.refresh(issue_status)
    
    return IssueStatusOut(
        project_id=issue_status.project_id,
        fingerprint=issue_status.fingerprint,
        status=issue_status.status,
        resolved_release=issue_status.resolved_release,
        resolved_at=issue_status.resolved_at,
        resolved_by_user_id=issue_status.resolved_by_user_id,
        notes=issue_status.notes,
        reopened=issue_status.reopened,
        created_at=issue_status.created_at,
        updated_at=issue_status.updated_at,
    )


@router.post("/api/user/projects/{project_id}/issues/bulk-status", response_model=dict)
def user_bulk_update_issue_status(
    project_id: int,
    payload: BulkIssueStatusUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update status for multiple issues."""
    require_owned_project(db, user=user, project_id=project_id)
    
    if payload.status not in ("open", "in_progress", "resolved", "ignored"):
        raise HTTPException(status_code=400, detail="Invalid status")
    
    updated_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    for fingerprint in payload.fingerprints:
        issue_status = db.get(IssueStatus, (project_id, fingerprint))
        if issue_status is None:
            issue_status = IssueStatus(
                project_id=project_id,
                fingerprint=fingerprint,
                status=payload.status,
                reopened=False,
            )
            db.add(issue_status)
        else:
            prev_status = issue_status.status
            issue_status.status = payload.status
        
        # Handle resolved status
        if payload.status == "resolved":
            issue_status.resolved_release = payload.resolved_release
            issue_status.resolved_at = now
            issue_status.resolved_by_user_id = user.id
            issue_status.reopened = False  # Clear reopened flag when resolving
        else:
            # Clear resolution fields if not resolved
            issue_status.resolved_release = None
            issue_status.resolved_at = None
            issue_status.resolved_by_user_id = None
            # If manually changing from resolved to open, mark as reopened
            if prev_status == "resolved" and payload.status == "open":
                issue_status.reopened = True
        
        # Update notes if provided
        if payload.notes is not None:
            issue_status.notes = payload.notes
        
        updated_count += 1
    
    db.commit()
    
    return {"updated": updated_count}
