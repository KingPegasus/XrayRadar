from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import RATE_LIMIT_EVENT_INGEST
from ..db import get_db
from ..rate_limit import get_rate_limit_key_token, limiter
from ..deps import authorize_ingest_for_project, require_admin, require_project_access
from ..fingerprinting import compute_fingerprint
from ..alert_scheduler import enqueue_error_alert_job
from ..mail_jobs import process_pending_email_jobs
from ..models import Event, IssueStatus, Project, Token
from ..notifications import get_alert_recipients, should_send_alert
from ..schemas import EventOut, ProjectCreate, ProjectOut
from ..usage import (
    get_user_event_count,
    get_user_event_limit,
    get_user_from_project,
    is_near_limit,
)

router = APIRouter()

# Breadcrumb limits
MAX_BREADCRUMBS = 100
MAX_BREADCRUMB_MESSAGE_LENGTH = 1024


def normalize_breadcrumbs(event: dict) -> dict:
    """Normalize breadcrumbs in event payload: limit count, truncate messages."""
    breadcrumbs = event.get("breadcrumbs")
    if not breadcrumbs or not isinstance(breadcrumbs, list):
        return event

    # Limit to most recent MAX_BREADCRUMBS
    if len(breadcrumbs) > MAX_BREADCRUMBS:
        breadcrumbs = breadcrumbs[-MAX_BREADCRUMBS:]

    normalized = []
    for bc in breadcrumbs:
        if not isinstance(bc, dict):
            continue

        normalized_bc = dict(bc)

        # Truncate message if too long
        if "message" in normalized_bc and isinstance(normalized_bc["message"], str):
            if len(normalized_bc["message"]) > MAX_BREADCRUMB_MESSAGE_LENGTH:
                normalized_bc["message"] = (
                    normalized_bc["message"][:MAX_BREADCRUMB_MESSAGE_LENGTH - 3] + "..."
                )

        # Ensure type has a default
        if "type" not in normalized_bc or not normalized_bc["type"]:
            normalized_bc["type"] = "default"

        # Ensure level has a default
        if "level" not in normalized_bc or not normalized_bc["level"]:
            normalized_bc["level"] = "info"

        normalized.append(normalized_bc)

    # Return a copy of the event with normalized breadcrumbs
    normalized_event = dict(event)
    normalized_event["breadcrumbs"] = normalized
    return normalized_event


@router.post("/api/projects", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    project = Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(id=project.id, name=project.name)


@router.post("/api/{project_id}/store/", response_model=dict)
@limiter.limit(RATE_LIMIT_EVENT_INGEST, key_func=get_rate_limit_key_token)
def store_event(
    request: Request,
    project_id: int,
    event: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
):
    env = (event.get("contexts") or {}).get("environment")
    authorize_ingest_for_project(
        project_id=project_id,
        environment=env,
        db=db,
        x_xrayradar_token=x_xrayradar_token,
    )

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

    # Check event storage limits for the project owner
    user = get_user_from_project(db, project)
    warning_message = None
    if user is not None:
        # Get current count before storing this event
        current_count = get_user_event_count(db, user.id)
        limit = get_user_event_limit(user)
        
        # Check if storing this event would exceed the limit
        if limit is not None and (current_count + 1) > limit:
            raise HTTPException(
                status_code=403,
                detail=f"Event storage limit exceeded. Current: {current_count}, Limit: {limit}. "
                f"Please upgrade your plan to store more events.",
            )
        
        # Check if approaching limit (after storing this event)
        if limit is not None and is_near_limit(current_count + 1, limit):
            percentage = int(((current_count + 1) / limit) * 100)
            warning_message = (
                f"Warning: You've used {percentage}% of your event storage limit "
                f"({current_count + 1}/{limit}). Consider upgrading your plan."
            )

    timestamp = event.get("timestamp")
    level = event.get("level") or "error"
    message = event.get("message") or ""

    try:
        ts = (
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if isinstance(timestamp, str)
            else datetime.now(timezone.utc)
        )
    except Exception:
        ts = datetime.now(timezone.utc)

    env = (event.get("contexts") or {}).get("environment")
    rel = (event.get("contexts") or {}).get("release")
    server_name = (event.get("contexts") or {}).get("server_name")
    fp = compute_fingerprint(event) if isinstance(event, dict) else None

    # Normalize breadcrumbs before storing
    normalized_event = normalize_breadcrumbs(event)

    row = Event(
        project_id=project_id,
        timestamp=ts,
        level=str(level),
        message=str(message)[:2048],
        environment=env,
        release=rel,
        server_name=server_name,
        fingerprint=fp,
        payload=normalized_event,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    # Auto-reopen logic: check if issue was resolved and should be reopened
    if fp:
        issue_status = db.get(IssueStatus, (project_id, fp))
        if issue_status and issue_status.status == "resolved":
            # If resolved_release is set and new event has release:
            if issue_status.resolved_release and rel:
                # Auto-reopen if same or different release (recurrence indicates fix didn't work)
                issue_status.status = "open"
                issue_status.reopened = True
                issue_status.resolved_release = None
                issue_status.resolved_at = None
                issue_status.resolved_by_user_id = None
                db.commit()
            # If resolved_release is set but new event has no release, stay resolved (conservative)
            # If resolved_release is null (resolved without release tracking), auto-reopen on any new event
            elif not issue_status.resolved_release:
                issue_status.status = "open"
                issue_status.reopened = True
                issue_status.resolved_at = None
                issue_status.resolved_by_user_id = None
                db.commit()
        # If status is "ignored", leave as-is (don't auto-reopen)

    # Email alerts: non-blocking, only for error level
    if level == "error":
        recipients = get_alert_recipients(db, project, environment=env)
        if recipients and should_send_alert(db, project_id, fp, str(level), environment=env):
            enqueued = enqueue_error_alert_job(
                db,
                project=project,
                recipients=recipients,
                environment=env,
                triggered_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            if enqueued:
                background_tasks.add_task(process_pending_email_jobs)

    response = {"id": str(row.id)}
    if warning_message:
        response["warning"] = warning_message
    return response


@router.get("/api/{project_id}/events", response_model=list[EventOut])
def list_events(
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Token = Depends(require_project_access),
):
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(Event.timestamp.desc())
        .limit(min(max(limit, 1), 200))
    )
    rows = db.execute(q).scalars().all()
    return [
        EventOut(
            id=r.id,
            project_id=r.project_id,
            timestamp=r.timestamp,
            level=r.level,
            message=r.message,
            payload=r.payload,
        )
        for r in rows
    ]


@router.get("/api/{project_id}/events/{event_id}", response_model=EventOut)
def get_event(
    project_id: int,
    event_id: UUID,
    db: Session = Depends(get_db),
    _: Token = Depends(require_project_access),
):
    row = db.get(Event, event_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Not found")
    return EventOut(
        id=row.id,
        project_id=row.project_id,
        timestamp=row.timestamp,
        level=row.level,
        message=row.message,
        payload=row.payload,
    )
