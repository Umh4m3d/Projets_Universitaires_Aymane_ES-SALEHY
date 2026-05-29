from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.course import Course
from app.models.absence import Absence
from app.schemas.absence import AbsenceCreate, AbsenceOut, AbsenceUpdate
from app.services.absence_service import (
    create_absence, get_absences_for_student,
    get_all_absences, justify_absence
)

router = APIRouter(prefix="/absences", tags=["Absences"])


def enrich_absences(absences: list, db) -> list[dict]:
    from app.models.user import User as UserModel
    result = []
    for a in absences:
        student  = db.query(UserModel).filter(UserModel.id == a.student_id).first()
        marker   = db.query(UserModel).filter(UserModel.id == a.marked_by_id).first()
        session  = db.query(SessionModel).filter(SessionModel.id == a.session_id).first()
        course   = db.query(Course).filter(Course.id == session.course_id).first() if session else None
        result.append({
            "id":             str(a.id),
            "session_id":     str(a.session_id),
            "student_id":     str(a.student_id),
            "marked_by_id":   str(a.marked_by_id),
            "is_justified":   a.is_justified,
            "justification":  a.justification if a.justification else None,
            "created_at":     str(a.created_at),
            "student_name":   student.full_name   if student else "Unknown",
            "marked_by_name": marker.full_name    if marker  else "Unknown",
            "session_date":   str(session.date)   if session else "Unknown",
            "course_name":    course.name         if course  else "Unknown",
        })
    return result


@router.post("/", response_model=AbsenceOut, status_code=201)
def mark_absence(
    data: AbsenceCreate,
    current_user: User = Depends(require_role("teacher", "secretary")),
    db: DBSession = Depends(get_db),
):
    return create_absence(db, data, marked_by=current_user)


@router.get("/mine")
def my_absences(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    absences = get_absences_for_student(db, current_user.id)
    return enrich_absences(absences, db)


@router.get("/stats")
def absence_stats(
    student_id: Optional[UUID] = Query(None),
    group_id:   Optional[UUID] = Query(None),
    date_from:  Optional[str]  = Query(None, description="YYYY-MM-DD"),
    date_to:    Optional[str]  = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    """
    Absence statistics with correct join handling.
    Joins SessionModel only once even when both date_from and date_to are supplied.
    """
    from app.models.student_profile import StudentProfile
    import datetime as dt

    # Determine whether we need to join Session for date filtering
    need_date_filter = bool(date_from or date_to)

    query = db.query(Absence)

    if student_id:
        query = query.filter(Absence.student_id == student_id)

    if group_id:
        profiles = db.query(StudentProfile).filter(
            StudentProfile.group_id == group_id
        ).all()
        ids = [p.user_id for p in profiles]
        if not ids:
            # No students in this group — return empty stats immediately
            return {
                "total": 0, "justified": 0, "unjustified": 0, "per_student": []
            }
        query = query.filter(Absence.student_id.in_(ids))

    # Join SessionModel ONCE for date filtering
    if need_date_filter:
        query = query.join(SessionModel, Absence.session_id == SessionModel.id)

        if date_from:
            try:
                d = dt.date.fromisoformat(date_from)
                query = query.filter(SessionModel.date >= d)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid date_from format (expected YYYY-MM-DD)")

        if date_to:
            try:
                d = dt.date.fromisoformat(date_to)
                query = query.filter(SessionModel.date <= d)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid date_to format (expected YYYY-MM-DD)")

    absences = query.all()

    total       = len(absences)
    justified   = sum(1 for a in absences if a.is_justified)
    unjustified = total - justified

    per_student: dict[str, dict] = {}
    for a in absences:
        sid = str(a.student_id)
        if sid not in per_student:
            student = db.query(User).filter(User.id == a.student_id).first()
            per_student[sid] = {
                "student_id":   sid,
                "student_name": student.full_name if student else "Unknown",
                "total":        0,
                "justified":    0,
                "unjustified":  0,
            }
        per_student[sid]["total"] += 1
        if a.is_justified:
            per_student[sid]["justified"] += 1
        else:
            per_student[sid]["unjustified"] += 1

    return {
        "total":       total,
        "justified":   justified,
        "unjustified": unjustified,
        "per_student": list(per_student.values()),
    }


@router.get("/")
def list_absences(
    session_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    absences = get_all_absences(db, session_id=session_id, student_id=student_id)
    return enrich_absences(absences, db)


@router.patch("/{absence_id}/justify", response_model=AbsenceOut)
def justify(
    absence_id: UUID,
    data: AbsenceUpdate,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    return justify_absence(db, absence_id, data)
