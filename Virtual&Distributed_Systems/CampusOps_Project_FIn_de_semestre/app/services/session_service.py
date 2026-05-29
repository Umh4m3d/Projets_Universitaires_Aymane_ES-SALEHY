# /services/session_service.py
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.session import Session
from app.models.course import Course
from app.models.group import Group
from app.models.user import User
from app.schemas.session import SessionCreate


def check_conflicts(db: DBSession, data: SessionCreate,
                    exclude_id: UUID = None) -> None:
    query = db.query(Session).filter(
        Session.date == data.date,
        Session.start_time < data.end_time,
        Session.end_time > data.start_time,
        Session.status == "approved",
    )
    if exclude_id:
        query = query.filter(Session.id != exclude_id)

    room_conflict = query.filter(Session.room == data.room).first()
    if room_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Room '{data.room}' is already booked from "
                   f"{room_conflict.start_time} to {room_conflict.end_time}"
        )

    teacher_conflict = query.filter(Session.teacher_id == data.teacher_id).first()
    if teacher_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Teacher already has a session from "
                   f"{teacher_conflict.start_time} to {teacher_conflict.end_time}"
        )

    group_conflict = query.filter(Session.group_id == data.group_id).first()
    if group_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This group already has a session from "
                   f"{group_conflict.start_time} to {group_conflict.end_time}"
        )


def validate_references(db: DBSession, data: SessionCreate) -> None:
    if not db.query(Course).filter(Course.id == data.course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")
    if not db.query(Group).filter(Group.id == data.group_id).first():
        raise HTTPException(status_code=404, detail="Group not found")
    teacher = db.query(User).filter(
        User.id == data.teacher_id,
        User.role == "teacher",
        User.is_active == True,
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or inactive")


def create_session(db: DBSession, data: SessionCreate,
                   submitted_by: User) -> Session:
    validate_references(db, data)
    check_conflicts(db, data)

    is_admin_or_secretary = submitted_by.role in ("admin", "secretary")
    session_status = "approved" if is_admin_or_secretary else "pending"

    session = Session(
        **data.model_dump(),
        status=session_status,
        submitted_by_id=submitted_by.id,
    )
    db.add(session)
    db.flush()

    if not is_admin_or_secretary:
        from app.models.user import User as UserModel
        course = db.query(Course).filter(Course.id == data.course_id).first()
        course_name = course.name if course else "Unknown"
        admins = db.query(UserModel).filter(
            UserModel.role == "admin",
            UserModel.is_active == True,
        ).all()
        for admin in admins:
            _notify(
                db, admin.id, "session_request",
                f"{submitted_by.full_name} has submitted a session request "
                f"for {course_name} on {data.date} "
                f"({str(data.start_time)[:5]}–{str(data.end_time)[:5]}, "
                f"Room {data.room}). Please review it in Session Requests."
            )

    db.commit()
    db.refresh(session)
    return session


def _notify(db: DBSession, user_id, notif_type: str, message: str):
    from app.models.notification import Notification
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        message=message,
        status="pending",
    )
    db.add(notif)


def approve_session(db: DBSession, session_id: UUID,
                    reviewed_by: User) -> Session:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "pending":
        raise HTTPException(status_code=400, detail="Session is not pending")

    from app.schemas.session import SessionCreate
    data = SessionCreate(
        course_id=session.course_id,
        teacher_id=session.teacher_id,
        group_id=session.group_id,
        room=session.room,
        date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
    )
    check_conflicts(db, data, exclude_id=session.id)

    session.status = "approved"
    db.flush()

    if session.submitted_by_id:
        course = db.query(Course).filter(Course.id == session.course_id).first()
        course_name = course.name if course else "Unknown"
        _notify(
            db, session.submitted_by_id, "session_approved",
            f"Your session request for {course_name} on {session.date} "
            f"({str(session.start_time)[:5]}–{str(session.end_time)[:5]}, "
            f"Room {session.room}) has been approved."
        )

    db.commit()
    db.refresh(session)
    return session


def reject_session(db: DBSession, session_id: UUID,
                   reason: str = None) -> Session:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "pending":
        raise HTTPException(status_code=400, detail="Session is not pending")

    session.status = "rejected"
    session.rejection_reason = reason.strip() if reason else None
    db.flush()

    if session.submitted_by_id:
        course = db.query(Course).filter(Course.id == session.course_id).first()
        course_name = course.name if course else "Unknown"
        reason_text = f" Reason: {reason.strip()}" if reason and reason.strip() else ""
        _notify(
            db, session.submitted_by_id, "session_rejected",
            f"Your session request for {course_name} on {session.date} "
            f"({str(session.start_time)[:5]}–{str(session.end_time)[:5]}, "
            f"Room {session.room}) has been rejected.{reason_text}"
        )

    db.commit()
    db.refresh(session)
    return session


def cancel_session(
    db: DBSession,
    session_id: UUID,
    cancelled_by: User,
    reason: str | None = None,
) -> Session:
    """
    Cancels an approved session.
    - Sets status to 'cancelled'.
    - Sends in-app notifications to every student in the group.
    - Sends cancellation emails to every student in the group.
    - The OpenClaw route calls this; teachers/admins can also call it directly.
    """
    from datetime import datetime, timezone

    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Only approved sessions can be cancelled (current status: {session.status})"
        )

    session.status = "cancelled"
    session.cancellation_reason = reason.strip() if reason else None
    session.cancelled_by_id = cancelled_by.id
    session.cancelled_at = datetime.now(timezone.utc)
    db.flush()

    # Resolve display names
    course = db.query(Course).filter(Course.id == session.course_id).first()
    course_name = course.name if course else "Unknown"
    start_str = str(session.start_time)[:5]
    end_str   = str(session.end_time)[:5]

    # Gather all students in the group
    from app.models.student_profile import StudentProfile
    profiles = db.query(StudentProfile).filter(
        StudentProfile.group_id == session.group_id
    ).all()

    student_ids = [p.user_id for p in profiles]
    students = db.query(User).filter(
        User.id.in_(student_ids),
        User.is_active == True,
    ).all() if student_ids else []

    for student in students:
        # In-app notification
        _notify(
            db, student.id, "session_cancelled",
            f"Session cancelled: {course_name} on {session.date} "
            f"({start_str}–{end_str}, Room {session.room})."
            + (f" Reason: {reason.strip()}" if reason and reason.strip() else "")
        )

        # Email
        try:
            from app.services.mail_service import send_session_cancellation
            recipient = student.notification_email
            if recipient:
              send_session_cancellation(
                to=recipient,
                full_name=student.full_name,
                course=course_name,
                date=str(session.date),
                start_time=start_str,
                end_time=end_str,
                room=session.room,
                reason=reason,)
        except Exception as e:
            from app.core.logging_config import logger
            logger.warning(f"Could not send cancellation email to {student.email}: {e}")

    db.commit()
    db.refresh(session)

    from app.core.logging_config import logger
    logger.info(
        f"Session cancelled: id={session_id} course={course_name} "
        f"date={session.date} by={cancelled_by.email} students_notified={len(students)}"
    )
    return session


def get_pending_sessions(db: DBSession) -> list:
    return db.query(Session).filter(
        Session.status == "pending"
    ).order_by(Session.date, Session.start_time).all()


def _get_sessions_filtered(db: DBSession, current_user: User,
                            date_from: date, date_to: date) -> list:
    from sqlalchemy import or_

    if current_user.role == "teacher":
        query = db.query(Session).filter(
            Session.date >= date_from,
            Session.date <= date_to,
        ).filter(
            or_(
                (Session.teacher_id == current_user.id) & (Session.status == "approved"),
                (Session.submitted_by_id == current_user.id) & (Session.status == "pending"),
            )
        )
    else:
        query = db.query(Session).filter(
            Session.date >= date_from,
            Session.date <= date_to,
            Session.status == "approved",
        )

    return query.order_by(Session.date, Session.start_time).all()


def get_sessions_today(db: DBSession, current_user: User) -> list:
    from datetime import date as date_type
    today = date_type.today()
    return _get_sessions_filtered(db, current_user, today, today)


def get_sessions_week(db: DBSession, current_user: User) -> list:
    from datetime import date as date_type
    today = date_type.today()
    week_end = today + timedelta(days=6)
    return _get_sessions_filtered(db, current_user, today, week_end)
