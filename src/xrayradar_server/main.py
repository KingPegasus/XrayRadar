import os
from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import Event, Project
from .schemas import EventIn, EventOut, ProjectCreate, ProjectOut

app = FastAPI(title="xrayradar-server")


@app.get("/health", response_model=dict)
def health() -> dict:
    return {
        "status": "ok",
        "auth_required": bool(os.getenv("XRAYRADAR_INGEST_TOKEN")),
    }


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.post("/api/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(id=project.id, name=project.name)


@app.post("/api/{project_id}/store/", response_model=dict)
def store_event(
    project_id: int,
    event: dict,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
):
    expected = os.getenv("XRAYRADAR_INGEST_TOKEN")
    if expected and x_xrayradar_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

    # SDK sends event_id + timestamp, but be defensive
    event_id = event.get("event_id")
    timestamp = event.get("timestamp")
    level = event.get("level") or "error"
    message = event.get("message") or ""

    try:
        ts = datetime.fromisoformat(timestamp.replace(
            "Z", "+00:00")) if isinstance(timestamp, str) else datetime.utcnow()
    except Exception:
        ts = datetime.utcnow()

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


@app.get("/api/{project_id}/events", response_model=list[EventOut])
def list_events(project_id: int, limit: int = 50, db: Session = Depends(get_db)):
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


@app.get("/api/{project_id}/events/{event_id}", response_model=EventOut)
def get_event(project_id: int, event_id: UUID, db: Session = Depends(get_db)):
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
