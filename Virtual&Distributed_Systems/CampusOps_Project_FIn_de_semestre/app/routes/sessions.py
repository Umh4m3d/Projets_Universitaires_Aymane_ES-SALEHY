from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from pydantic import BaseModel
from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.session import SessionCreate, SessionOut
from app.services.session_service import (
    create_session, get_sessions_today, get_sessions_week,
    approve_session, reject_session, get_pending_sessions,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def enrich(sessions: list, db: DBSession) -> list[dict]:
    from app.models.course import Course
    from app.models.group import Group
    from app.models.user import User as UserModel

    result = []
    for s in sessions:
        course  = db.query(Course).filter(Course.id == s.course_id).first()
        group   = db.query(Group).filter(Group.id == s.group_id).first()
        teacher = db.query(UserModel).filter(UserModel.id == s.teacher_id).first()
        result.append({
            "id":               str(s.id),
            "room":             s.room,
            "date":             str(s.date),
            "start_time":       str(s.start_time),
            "end_time":         str(s.end_time),
            "status":           s.status,
            "rejection_reason": s.rejection_reason,
            "course_id":        str(s.course_id),
            "teacher_id":       str(s.teacher_id),
            "group_id":         str(s.group_id),
            "course_name":      course.name       if course  else "Unknown",
            "teacher_name":     teacher.full_name if teacher else "Unknown",
            "group_name":       group.name        if group   else "Unknown",
            "created_at":       str(s.created_at),
        })
    return result


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create(
    data: SessionCreate,
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    return create_session(db, data, submitted_by=current_user)


@router.get("/pending")
def pending(
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    return enrich(get_pending_sessions(db), db)


@router.get("/by-teacher/{teacher_id}")
def by_teacher(
    teacher_id: str,
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    from app.models.session import Session as SessionModel
    from uuid import UUID
    from datetime import date as date_type

    query = db.query(SessionModel).filter(
        SessionModel.teacher_id == UUID(teacher_id),
        SessionModel.status == "approved",
    )
    if date_from:
        query = query.filter(SessionModel.date >= date_type.fromisoformat(date_from))
    if date_to:
        query = query.filter(SessionModel.date <= date_type.fromisoformat(date_to))
    return enrich(query.order_by(SessionModel.date, SessionModel.start_time).all(), db)


@router.get("/by-group/{group_id}")
def by_group(
    group_id: str,
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    from app.models.session import Session as SessionModel
    from uuid import UUID
    from datetime import date as date_type

    query = db.query(SessionModel).filter(
        SessionModel.group_id == UUID(group_id),
        SessionModel.status == "approved",
    )
    if date_from:
        query = query.filter(SessionModel.date >= date_type.fromisoformat(date_from))
    if date_to:
        query = query.filter(SessionModel.date <= date_type.fromisoformat(date_to))
    return enrich(query.order_by(SessionModel.date, SessionModel.start_time).all(), db)


@router.get("/by-student/{student_id}")
def by_student(
    student_id: str,
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    from app.models.session import Session as SessionModel
    from app.models.student_profile import StudentProfile
    from uuid import UUID
    from datetime import date as date_type

    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == UUID(student_id)
    ).first()
    if not profile or not profile.group_id:
        return []

    query = db.query(SessionModel).filter(
        SessionModel.group_id == profile.group_id,
        SessionModel.status == "approved",
    )
    if date_from:
        query = query.filter(SessionModel.date >= date_type.fromisoformat(date_from))
    if date_to:
        query = query.filter(SessionModel.date <= date_type.fromisoformat(date_to))
    return enrich(query.order_by(SessionModel.date, SessionModel.start_time).all(), db)


@router.patch("/{session_id}/approve")
def approve(
    session_id: str,
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    from uuid import UUID
    session = approve_session(db, UUID(session_id), current_user)
    return enrich([session], db)[0]


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.patch("/{session_id}/reject")
def reject(
    session_id: str,
    data: RejectRequest = RejectRequest(),
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    from uuid import UUID
    session = reject_session(db, UUID(session_id), reason=data.reason)
    return enrich([session], db)[0]


@router.delete("/{session_id}", status_code=200)
def delete_session(
    session_id: str,
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    """
    Delete a session.
    - Admin / Secretary: can delete any session.
    - Teacher: can only delete sessions they submitted themselves,
      and only if still pending (not yet approved).
    """
    from uuid import UUID
    from app.models.session import Session as SessionModel
    from app.models.absence import Absence

    sid = UUID(session_id)
    session = db.query(SessionModel).filter(SessionModel.id == sid).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Teachers may only delete their own pending requests
    if current_user.role == "teacher":
        if session.submitted_by_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete sessions you submitted yourself"
            )
        if session.status == "approved":
            raise HTTPException(
                status_code=400,
                detail="Approved sessions cannot be deleted. Ask an admin."
            )

    # Block deletion if absences are already recorded for this session
    has_absences = db.query(Absence).filter(
        Absence.session_id == sid
    ).first()
    if has_absences:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a session that has absence records. "
                   "Remove the absences first or deactivate the session."
        )

    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}


@router.get("/today")
def today(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return enrich(get_sessions_today(db, current_user), db)


@router.get("/week")
def week(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return enrich(get_sessions_week(db, current_user), db)
