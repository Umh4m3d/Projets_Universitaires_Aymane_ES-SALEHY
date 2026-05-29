# /services/absence_service.py
from datetime import datetime, timezone, date as date_type
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status

from app.models.absence import Absence
from app.models.notification import Notification
from app.models.session import Session
from app.models.user import User
from app.schemas.absence import AbsenceCreate, AbsenceUpdate
from app.core.logging_config import logger


def validate_session_and_student(
    db: DBSession, session_id: UUID, student_id: UUID
) -> tuple[Session, User]:

    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    student = db.query(User).filter(
        User.id == student_id,
        User.role == "student",
        User.is_active == True
    ).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found or inactive"
        )

    return session, student


def create_absence(
    db: DBSession,
    data: AbsenceCreate,
    marked_by: User
) -> Absence:

    session, student = validate_session_and_student(
        db, data.session_id, data.student_id
    )

    existing = db.query(Absence).filter(
        Absence.session_id == data.session_id,
        Absence.student_id == data.student_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Absence already recorded for this student in this session"
        )

    absence = Absence(
        session_id=data.session_id,
        student_id=data.student_id,
        marked_by_id=marked_by.id,
        justification=data.justification,
    )
    db.add(absence)
    db.flush()

    # ── In-app notification ───────────────────────────────────────────────────
    message = (
        f"Absence recorded: {student.full_name} was absent "
        f"from session on {session.date} "
        f"(Room {session.room}, {session.start_time} - {session.end_time}). "
        f"Marked by: {marked_by.full_name}."
    )
    notification = Notification(
        user_id=student.id,
        type="absence",
        message=message,
        status="pending",
    )
    db.add(notification)

    # ── Email student ─────────────────────────────────────────────────────────
    try:
        from app.services.mail_service import send_absence_notification
        from app.models.course import Course

        recipient = student.notification_email
        course = db.query(Course).filter(Course.id == session.course_id).first()
        course_name = course.name if course else "Unknown"
        if recipient:
          send_absence_notification(
            to=recipient,
            full_name=student.full_name,
            course=course_name,
            date=str(session.date),
            room=session.room,)
    except Exception as e:
        logger.warning(f"Could not send absence email to student: {e}")

    # ── Email parent if student has more than 1 absence today ─────────────────
    # Commit the new absence first so the count below includes it
    db.commit()
    db.refresh(absence)

    try:
        _maybe_alert_parent(db, student, session.date)
    except Exception as e:
        logger.warning(f"Could not send parent absence alert: {e}")

    logger.info(
        f"Absence recorded: student={student.email} "
        f"session={session.id} marked_by={marked_by.email}"
    )

    return absence


def _maybe_alert_parent(db: DBSession, student: User, session_date) -> None:
    """
    If the student now has more than 1 absence on `session_date`,
    email their parent/guardian (from student_profile.parent_email).
    """
    from app.models.student_profile import StudentProfile
    from app.models.session import Session as SessionModel
    from app.models.course import Course

    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == student.id
    ).first()

    if not profile or not profile.parent_email:
        return

    # Count all absences for this student on the same calendar day
    absences_today = (
        db.query(Absence)
        .join(SessionModel, Absence.session_id == SessionModel.id)
        .filter(
            Absence.student_id == student.id,
            SessionModel.date == session_date,
        )
        .all()
    )

    count = len(absences_today)
    if count <= 1:
        return  # First absence — individual email already sent, parent silent

    # Gather course names for each absence today
    course_names = []
    for ab in absences_today:
        sess = db.query(SessionModel).filter(SessionModel.id == ab.session_id).first()
        if sess:
            course = db.query(Course).filter(Course.id == sess.course_id).first()
            course_names.append(course.name if course else "Unknown course")

    from app.services.mail_service import send_parent_absence_alert
    send_parent_absence_alert(
        to=profile.parent_email,
        parent_name="Parent/Guardian",
        student_name=student.full_name,
        absence_count=count,
        date=str(session_date),
        courses=course_names,
    )
    logger.info(
        f"Parent absence alert sent: student={student.email} "
        f"count={count} date={session_date}"
    )


def get_absences_for_student(db: DBSession, student_id: UUID) -> list[Absence]:
    return (
        db.query(Absence)
        .filter(Absence.student_id == student_id)
        .order_by(Absence.created_at.desc())
        .all()
    )


def get_all_absences(
    db: DBSession,
    session_id: Optional[UUID] = None,
    student_id: Optional[UUID] = None,
) -> list[Absence]:
    query = db.query(Absence)
    if session_id:
        query = query.filter(Absence.session_id == session_id)
    if student_id:
        query = query.filter(Absence.student_id == student_id)
    return query.order_by(Absence.created_at.desc()).all()


def justify_absence(
    db: DBSession,
    absence_id: UUID,
    data: AbsenceUpdate,
) -> Absence:
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Absence not found")

    absence.is_justified = data.is_justified
    absence.justification = (
        data.justification.strip()
        if data.justification and data.justification.strip()
        else None
    )

    db.commit()
    db.refresh(absence)
    logger.info(f"Absence {absence_id} justified={data.is_justified}")
    return absence
