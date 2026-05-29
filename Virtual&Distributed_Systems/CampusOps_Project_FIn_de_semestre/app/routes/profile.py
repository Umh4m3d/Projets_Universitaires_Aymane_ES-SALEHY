# /routes/profile.py
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.change_request import ChangeRequest
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/profile", tags=["Profile"])


class ChangeRequestCreate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangeRequestOut(BaseModel):
    id: UUID
    field: str
    old_value: str
    new_value: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ChangeRequestReview(BaseModel):
    action: str  # "approve" or "reject"


class NotificationEmailUpdate(BaseModel):
    notification_email: Optional[EmailStr] = None


class ParentEmailUpdate(BaseModel):
    parent_email: Optional[EmailStr] = None


@router.post("/request-changes", response_model=list[ChangeRequestOut])
def request_changes(
    data: ChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if not data.full_name and not data.email:
        raise HTTPException(status_code=400, detail="No changes provided")

    created = []

    if data.full_name and data.full_name.strip() != current_user.full_name:
        db.query(ChangeRequest).filter(
            ChangeRequest.user_id == current_user.id,
            ChangeRequest.field == "full_name",
            ChangeRequest.status == "pending",
        ).delete()
        req = ChangeRequest(
            user_id=current_user.id,
            field="full_name",
            old_value=current_user.full_name,
            new_value=data.full_name.strip(),
        )
        db.add(req)
        created.append(req)

    if data.email and data.email.lower() != current_user.email:
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        db.query(ChangeRequest).filter(
            ChangeRequest.user_id == current_user.id,
            ChangeRequest.field == "email",
            ChangeRequest.status == "pending",
        ).delete()
        req = ChangeRequest(
            user_id=current_user.id,
            field="email",
            old_value=current_user.email,
            new_value=data.email.lower(),
        )
        db.add(req)
        created.append(req)

    if not created:
        raise HTTPException(status_code=400, detail="No changes detected")

    db.commit()
    for r in created:
        db.refresh(r)
    return created


@router.get("/my-requests", response_model=list[ChangeRequestOut])
def my_requests(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return db.query(ChangeRequest).filter(
        ChangeRequest.user_id == current_user.id
    ).order_by(ChangeRequest.created_at.desc()).limit(10).all()


@router.get("/pending-requests", response_model=list[dict])
def pending_requests(
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    requests = db.query(ChangeRequest).filter(
        ChangeRequest.status == "pending"
    ).order_by(ChangeRequest.created_at).all()

    result = []
    for r in requests:
        result.append({
            "id": str(r.id),
            "user_name": r.user.full_name,
            "user_email": r.user.email,
            "field": r.field,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "status": r.status,
            "created_at": str(r.created_at),
        })
    return result


@router.patch("/{request_id}/review")
def review_request(
    request_id: UUID,
    data: ChangeRequestReview,
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    if data.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    req = db.query(ChangeRequest).filter(ChangeRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already reviewed")

    req.status = "approved" if data.action == "approve" else "rejected"
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    if data.action == "approve":
        user = db.query(User).filter(User.id == req.user_id).first()
        if req.field == "full_name":
            user.full_name = req.new_value
        elif req.field == "email":
            user.email = req.new_value

    db.commit()
    return {"message": f"Request {req.status}"}


@router.patch("/notification-email")
def update_notification_email(
    data: NotificationEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Lets any user set their personal (real) email for notifications and password resets.
    """
    current_user.notification_email = data.notification_email.lower() if data.notification_email else None
    db.commit()
    db.refresh(current_user)
    return {"message": "Notification email updated", "notification_email": current_user.notification_email}


@router.patch("/parent-email")
def update_parent_email(
    data: ParentEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Lets a student update their own parent/guardian email on their student profile.
    This email receives absence and payment notifications on their behalf.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can update a parent email")

    from app.models.student_profile import StudentProfile
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found. Contact your secretary.")

    profile.parent_email = data.parent_email.lower() if data.parent_email else None
    db.commit()
    db.refresh(profile)
    return {"message": "Parent email updated", "parent_email": profile.parent_email}


@router.get("/my-student-profile")
def get_my_student_profile(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Returns the student profile for the current user (students only)."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a student profile")

    from app.models.student_profile import StudentProfile
    from app.models.group import Group
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    if not profile:
        return None  # profile not yet created by secretary

    group = db.query(Group).filter(Group.id == profile.group_id).first() if profile.group_id else None
    return {
        "id":            str(profile.id),
        "establishment": profile.establishment,
        "group_name":    group.name if group else None,
        "year":          profile.year,
        "parent_email":  profile.parent_email,
    }
