"""User API: dashboard stats."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import Event, Project, User
from ...deps import require_user
from ...schemas import (
    DashboardStatsOut,
    DashboardTotalsOut,
    DashboardTrendOut,
    DashboardUniqueIssuesOut,
    TopErrorOut,
)
router = APIRouter()


@router.get("/api/user/dashboard/stats", response_model=DashboardStatsOut)
def user_get_dashboard_stats(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get error statistics across all user projects: totals (24h/7d/30d), unique issues, trend, top 5 errors."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    t_24h = now - timedelta(hours=24)
    t_7d = now - timedelta(days=7)
    t_30d = now - timedelta(days=30)
    t_14d = now - timedelta(days=14)
    t_60d = now - timedelta(days=60)

    user_projects = select(Project.id).where(Project.owner_user_id == user.id)
    base = Event.project_id.in_(user_projects) & (Event.level == "error")

    def count_events(since):
        q = (
            select(func.count(Event.id))
            .select_from(Event)
            .where(base)
            .where(Event.timestamp >= since)
        )
        return db.execute(q).scalar() or 0

    last_24h = count_events(t_24h)
    last_7d = count_events(t_7d)
    last_30d = count_events(t_30d)

    base_fp = base & Event.fingerprint.is_not(None)

    def count_unique(since):
        q = (
            select(func.count(func.distinct(Event.fingerprint)))
            .select_from(Event)
            .where(base_fp)
            .where(Event.timestamp >= since)
        )
        return db.execute(q).scalar() or 0

    unique_24h = count_unique(t_24h)
    unique_7d = count_unique(t_7d)
    unique_30d = count_unique(t_30d)

    prev_7d = db.execute(
        select(func.count(Event.id))
        .select_from(Event)
        .where(base)
        .where(Event.timestamp >= t_14d)
        .where(Event.timestamp < t_7d)
    ).scalar() or 0

    def trend(current: int, previous: int) -> tuple[float, str]:
        if previous == 0:
            return (0.0 if current == 0 else 100.0, "up" if current > 0 else "same")
        pct = ((current - previous) / previous) * 100.0
        direction = "up" if current > previous else ("down" if current < previous else "same")
        return (round(pct, 1), direction)

    pct_7d, dir_7d = trend(last_7d, prev_7d)

    prev_30d = db.execute(
        select(func.count(Event.id))
        .select_from(Event)
        .where(base)
        .where(Event.timestamp >= t_60d)
        .where(Event.timestamp < t_30d)
    ).scalar() or 0

    pct_30d, dir_30d = trend(last_30d, prev_30d)

    top_agg = (
        select(
            Event.project_id,
            Event.fingerprint,
            func.count(Event.id).label("cnt"),
        )
        .where(base_fp)
        .where(Event.timestamp >= t_30d)
        .group_by(Event.project_id, Event.fingerprint)
        .order_by(func.count(Event.id).desc())
        .limit(5)
    )
    top_rows = db.execute(top_agg).all()

    top_5_errors: list[TopErrorOut] = []
    for proj_id, fp, cnt in top_rows:
        if fp is None:
            continue
        proj = db.get(Project, proj_id)
        proj_name = proj.name if proj else ""
        latest = (
            db.execute(
                select(Event.message)
                .where(Event.project_id == proj_id)
                .where(Event.fingerprint == fp)
                .where(Event.timestamp >= t_30d)
                .order_by(Event.timestamp.desc())
                .limit(1)
            )
        ).scalars().first()
        message = latest or ""
        top_5_errors.append(
            TopErrorOut(
                fingerprint=str(fp),
                message=message,
                count=int(cnt or 0),
                project_id=proj_id,
                project_name=proj_name,
            )
        )

    daily_q = (
        select(
            func.date(Event.timestamp).label("dt"),
            func.count(Event.id).label("cnt"),
        )
        .where(base)
        .where(Event.timestamp >= t_30d)
        .group_by(func.date(Event.timestamp))
    )
    daily_rows = db.execute(daily_q).all()
    trend_daily: dict[str, int] = {}
    for date_obj, cnt in daily_rows:
        if isinstance(date_obj, datetime):
            date_str = date_obj.date().isoformat()
        elif hasattr(date_obj, "isoformat"):
            date_str = date_obj.isoformat()
        else:
            date_str = str(date_obj)
            if " " in date_str or "T" in date_str:
                date_str = date_str.split()[0].split("T")[0]
        trend_daily[date_str] = int(cnt or 0)

    return DashboardStatsOut(
        totals=DashboardTotalsOut(last_24h=last_24h, last_7d=last_7d, last_30d=last_30d),
        unique_issues=DashboardUniqueIssuesOut(
            last_24h=unique_24h, last_7d=unique_7d, last_30d=unique_30d
        ),
        trend_7d=DashboardTrendOut(
            current=last_7d, previous=prev_7d, percent_change=pct_7d, direction=dir_7d
        ),
        trend_30d=DashboardTrendOut(
            current=last_30d, previous=prev_30d, percent_change=pct_30d, direction=dir_30d
        ),
        top_5_errors=top_5_errors,
        trend_daily=trend_daily,
    )
