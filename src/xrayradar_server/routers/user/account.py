"""User API: deletion request."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import DeletionRequest, User
from ...deps import require_user, require_verified_user
from ...schemas import DeletionRequestCreate, DeletionRequestOut

router = APIRouter()


@router.post("/api/user/deletion-request", response_model=DeletionRequestOut)
def user_request_deletion(
    payload: DeletionRequestCreate,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Request account deletion. Admin will review and fulfill."""
    existing = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Deletion request already pending")

    req = DeletionRequest(user_id=user.id, reason=payload.reason)
    db.add(req)
    db.commit()
    db.refresh(req)

    return DeletionRequestOut(
        id=req.id,
        user_id=req.user_id,
        reason=req.reason,
        created_at=req.created_at,
        fulfilled_at=req.fulfilled_at,
        cancelled_at=req.cancelled_at,
    )


@router.get("/api/user/deletion-request", response_model=DeletionRequestOut | None)
def user_get_deletion_request(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get the current pending deletion request, if any."""
    req = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
        .order_by(DeletionRequest.id.desc())
    ).scalars().first()
    if req is None:
        return None
    return DeletionRequestOut(
        id=req.id,
        user_id=req.user_id,
        reason=req.reason,
        created_at=req.created_at,
        fulfilled_at=req.fulfilled_at,
        cancelled_at=req.cancelled_at,
    )


@router.delete("/api/user/deletion-request")
def user_cancel_deletion_request(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending deletion request."""
    req = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
        .order_by(DeletionRequest.id.desc())
    ).scalars().first()
    if req is None:
        raise HTTPException(status_code=404, detail="No pending deletion request")
    req.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"ok": True}
