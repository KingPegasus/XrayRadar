from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import authorize_ingest_for_project, require_admin, require_project_access
from ..models import Event, Project, Token
from ..schemas import EventOut, ProjectCreate, ProjectOut

router = APIRouter()


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
def store_event(
    project_id: int,
    event: dict,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
):
    authorize_ingest_for_project(
        project_id=project_id,
        db=db,
        x_xrayradar_token=x_xrayradar_token,
    )

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

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

    row = Event(
        project_id=project_id,
        timestamp=ts,
        level=str(level),
        message=str(message)[:2048],
        environment=env,
        release=rel,
        server_name=server_name,
        payload=event,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {"id": str(row.id)}


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
