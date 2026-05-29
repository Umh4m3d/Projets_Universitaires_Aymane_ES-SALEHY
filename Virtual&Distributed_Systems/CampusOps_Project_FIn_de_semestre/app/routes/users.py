from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role, require_bot_secret
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


def has_linked_data(user: User, db: Session) -> bool:
    """Check if a user has any linked records that prevent deletion."""
    from app.models.session import Session as SessionModel
    from app.models.absence import Absence
    from app.models.payment import Payment

    if user.role == "teacher":
        return db.query(SessionModel).filter(
            SessionModel.teacher_id == user.id
        ).first() is not None

    if user.role == "student":
        has_absences = db.query(Absence).filter(
            Absence.student_id == user.id
        ).first() is not None
        has_payments = db.query(Payment).filter(
            Payment.student_id == user.id
        ).first() is not None
        return has_absences or has_payments

    return False


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/students")
def list_students(
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: Session = Depends(get_db),
):
    from app.models.student_profile import StudentProfile
    from uuid import UUID as PyUUID

    if group_id:
        try:
            gid = PyUUID(group_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid group_id")
        profiles = db.query(StudentProfile).filter(
            StudentProfile.group_id == gid
        ).all()
        user_ids = [p.user_id for p in profiles]
        if not user_ids:
            return []
        return db.query(User).filter(
            User.id.in_(user_ids),
            User.is_active == True,
        ).order_by(User.full_name).all()

    return db.query(User).filter(
        User.role == "student",
        User.is_active == True,
    ).order_by(User.full_name).all()


@router.get("/staff")
def list_staff(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Returns admins and secretaries only."""
    return db.query(User).filter(
        User.role.in_(["admin", "secretary"])
    ).order_by(User.created_at).all()


@router.get("/teachers")
def list_teachers(
    current_user: User = Depends(require_role("admin", "secretary")),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(
        User.role == "teacher"
    ).order_by(User.full_name).all()


@router.get("/")
def list_users(
    current_user: User = Depends(require_role("admin", "secretary")),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at).all()


@router.get("/by-chat-id/{chat_id}", response_model=UserOut)
def get_by_chat_id(
    chat_id: str,
    _: bool = Depends(require_bot_secret),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.telegram_chat_id == chat_id,
        User.is_active == True,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user linked to this chat")
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400,
                            detail="You cannot deactivate your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is already inactive")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400,
                            detail="You cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if has_linked_data(user, db):
        raise HTTPException(
            status_code=409,
            detail="This user has linked records (sessions, absences, or payments). "
                   "Deactivate instead of deleting to preserve the audit trail."
        )

    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted permanently"}
