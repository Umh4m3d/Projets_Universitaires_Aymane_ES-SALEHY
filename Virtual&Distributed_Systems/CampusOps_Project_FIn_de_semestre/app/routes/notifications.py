from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    message: str
    status: str

    model_config = {"from_attributes": True}


class NotificationStatusUpdate(BaseModel):
    status: str


@router.get("/pending", response_model=list[NotificationOut])
def get_pending(
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    return db.query(Notification).filter(
        Notification.status == "pending"
    ).order_by(Notification.created_at).all()


@router.patch("/{notification_id}", response_model=NotificationOut)
def update_status(
    notification_id: UUID,
    data: NotificationStatusUpdate,
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notif:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.status = data.status
    if data.status == "sent":
        notif.sent_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notif)
    return notif


@router.get("/mine", response_model=list[NotificationOut])
def my_notifications(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
