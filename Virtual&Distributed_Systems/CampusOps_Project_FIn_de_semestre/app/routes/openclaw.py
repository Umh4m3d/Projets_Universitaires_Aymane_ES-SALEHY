# app/routes/openclaw.py
"""
Routes exclusively for the OpenClaw orchestrator.
Protected by X-OpenClaw-Key header (shared secret, not JWT).

Endpoints:
  POST /openclaw/send-weekly-planning   → email next-week schedule to each teacher
  POST /openclaw/check-overdue-payments → mark overdue + create follow-up tasks
  POST /openclaw/process-cancellations  → dispatch cancellation emails (idempotent)
  POST /openclaw/cancel-session         → cancel a specific session by ID
"""

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.logging_config import logger
from app.db.session import get_db
from app.models.absence import Absence
from app.models.followup_task import FollowUpTask
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.session import Session as SessionModel
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.models.course import Course
from app.models.group import Group

router = APIRouter(prefix="/openclaw", tags=["OpenClaw"])


# ── Auth guard ────────────────────────────────────────────────────────────────

def require_openclaw_key(x_openclaw_key: str = Header(default="")):
    if not settings.OPENCLAW_KEY:
        raise HTTPException(status_code=503, detail="OPENCLAW_KEY not configured on server")
    if x_openclaw_key != settings.OPENCLAW_KEY:
        raise HTTPException(status_code=403, detail="Invalid OpenClaw key")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Weekly planning email — runs Sunday 12:00
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/send-weekly-planning")
def send_weekly_planning(
    _: bool = Depends(require_openclaw_key),
    db: DBSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Sends each teacher their next-week schedule by email.
    Next week = Monday to Sunday of the coming week.
    """
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    next_sunday = next_monday + timedelta(days=6)

    sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.status == "approved",
            SessionModel.date >= next_monday,
            SessionModel.date <= next_sunday,
        )
        .order_by(SessionModel.date, SessionModel.start_time)
        .all()
    )

    by_teacher: dict[str, list] = {}
    for s in sessions:
        by_teacher.setdefault(str(s.teacher_id), []).append(s)

    sent = 0
    errors = 0
    for teacher_id, teacher_sessions in by_teacher.items():
        teacher = db.query(User).filter(User.id == teacher_id, User.is_active == True).first()
        if not teacher:
            continue

        recipient = teacher.notification_email
        if not recipient:
            logger.info(f"[OpenClaw] Skipping planning email for {teacher.email} — no notification_email set")
            continue

        session_dicts = []
        for s in teacher_sessions:
            course = db.query(Course).filter(Course.id == s.course_id).first()
            group  = db.query(Group).filter(Group.id == s.group_id).first()
            session_dicts.append({
                "date":        str(s.date),
                "start_time":  str(s.start_time),
                "end_time":    str(s.end_time),
                "room":        s.room,
                "course_name": course.name if course else "Unknown",
                "group_name":  group.name  if group  else "Unknown",
            })

        try:
            from app.services.mail_service import send_weekly_schedule
            send_weekly_schedule(
                to=recipient,
                full_name=teacher.full_name,
                sessions=session_dicts,
                week_from=str(next_monday),
                week_to=str(next_sunday),
            )
            sent += 1
            logger.info(f"[OpenClaw] Weekly planning sent to {teacher.email} ({len(teacher_sessions)} sessions)")
        except Exception as e:
            errors += 1
            logger.warning(f"[OpenClaw] Could not send planning to {teacher.email}: {e}")

    return {
        "message":          f"Weekly planning sent to {sent} teacher(s)",
        "teachers_emailed": sent,
        "errors":           errors,
        "week_from":        str(next_monday),
        "week_to":          str(next_sunday),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Overdue payment check + follow-up tasks
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/check-overdue-payments")
def check_overdue_payments_and_tasks(
    _: bool = Depends(require_openclaw_key),
    db: DBSession = Depends(get_db),
) -> dict[str, Any]:
    """
    1. Marks pending/partial payments past their due_date as 'overdue'.
    2. Sends student a notification + email.
    3. Creates a FollowUpTask for an admin/secretary.
    Idempotent — payments already 'overdue' are not double-processed.
    """
    today = date.today()
    payments = (
        db.query(Payment)
        .filter(
            Payment.status.in_(["pending", "partial"]),
            Payment.due_date < today,
        )
        .all()
    )

    admin = db.query(User).filter(
        User.role.in_(["admin", "secretary"]),
        User.is_active == True,
    ).first()

    overdue_count = 0
    tasks_created = 0

    for payment in payments:
        payment.status = "overdue"
        db.flush()

        student = db.query(User).filter(User.id == payment.student_id).first()
        if not student:
            continue

        # In-app notification
        db.add(Notification(
            user_id=payment.student_id,
            type="payment_overdue",
            message=(
                f"Payment overdue: {student.full_name} has an unpaid "
                f"{payment.type} fee of {payment.amount} DH "
                f"due on {payment.due_date}. Please settle as soon as possible."
            ),
            status="pending",
        ))

        # Email student
        recipient = student.notification_email
        if recipient:
            try:
                from app.services.mail_service import send_payment_overdue_notification
                send_payment_overdue_notification(
                    to=recipient,
                    full_name=student.full_name,
                    amount=payment.amount,
                    month=payment.month,
                    due_date=str(payment.due_date),
                )
            except Exception as e:
                logger.warning(f"[OpenClaw] Could not send overdue email to {student.email}: {e}")
        else:
            logger.info(f"[OpenClaw] Skipping overdue email for {student.email} — no notification_email set")

        # Follow-up task (only if one doesn't already exist for this payment)
        existing_task = db.query(FollowUpTask).filter(
            FollowUpTask.payment_id == payment.id,
            FollowUpTask.task_type  == "payment_followup",
            FollowUpTask.status     == "open",
        ).first()

        if not existing_task:
            db.add(FollowUpTask(
                assigned_to_id=admin.id if admin else None,
                subject_user_id=payment.student_id,
                payment_id=payment.id,
                task_type="payment_followup",
                title=f"Payment overdue — {student.full_name}",
                description=(
                    f"{student.full_name} has an overdue {payment.type} payment "
                    f"of {payment.amount} DH (month: {payment.month or '—'}) "
                    f"due since {payment.due_date}. Please follow up."
                ),
                status="open",
            ))
            tasks_created += 1

        overdue_count += 1
        logger.warning(
            f"[OpenClaw] Payment overdue: student={student.email} "
            f"amount={payment.amount} due={payment.due_date}"
        )

    db.commit()
    return {
        "message":       f"{overdue_count} payment(s) marked overdue, {tasks_created} task(s) created",
        "overdue_count": overdue_count,
        "tasks_created": tasks_created,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Cancel a specific session
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/cancel-session")
def cancel_session_route(
    body: dict,
    _: bool = Depends(require_openclaw_key),
    db: DBSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Cancels an approved session by ID.
    Body: {"session_id": "<uuid>", "reason": "optional reason"}
    """
    from uuid import UUID
    from app.services.session_service import cancel_session as svc_cancel_session

    session_id = body.get("session_id")
    reason     = body.get("reason")

    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")

    admin = db.query(User).filter(
        User.role.in_(["admin", "secretary"]),
        User.is_active == True,
    ).first()
    if not admin:
        raise HTTPException(status_code=503, detail="No admin user found to act as canceller")

    try:
        session = svc_cancel_session(db, UUID(session_id), cancelled_by=admin, reason=reason)
        # Idempotency record so process-cancellations poller skips this one
        db.add(FollowUpTask(
            session_id=session.id,
            task_type="cancellation_followup",
            title=f"Cancellation via API — {session_id[:8]}",
            description="Cancelled and notified immediately via cancel-session endpoint.",
            status="done",
        ))
        db.commit()
        return {
            "message":    f"Session {session_id} cancelled successfully",
            "session_id": session_id,
            "status":     session.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Process cancellation notifications — idempotent poll
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/process-cancellations")   # ← THE MISSING DECORATOR (was a bare function)
def process_cancellations(
    _: bool = Depends(require_openclaw_key),
    db: DBSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Finds cancelled sessions whose students have NOT yet been emailed
    (tracked via a FollowUpTask with type='cancellation_followup' + status='done').
    Sends emails and marks the task done so the job is idempotent.
    """
    cancelled_sessions = (
        db.query(SessionModel)
        .filter(SessionModel.status == "cancelled")
        .all()
    )

    processed = 0

    for session in cancelled_sessions:
        # Skip if already handled
        already_done = db.query(FollowUpTask).filter(
            FollowUpTask.session_id == session.id,
            FollowUpTask.task_type  == "cancellation_followup",
            FollowUpTask.status     == "done",
        ).first()
        if already_done:
            continue

        course     = db.query(Course).filter(Course.id == session.course_id).first()
        course_name = course.name if course else "Unknown"
        start_str  = str(session.start_time)[:5]
        end_str    = str(session.end_time)[:5]

        profiles    = db.query(StudentProfile).filter(StudentProfile.group_id == session.group_id).all()
        student_ids = [p.user_id for p in profiles]
        students    = (
            db.query(User).filter(User.id.in_(student_ids), User.is_active == True).all()
            if student_ids else []
        )

        email_errors = 0
        for student in students:
            # In-app notification (skip if already created by session_service)
            already_notified = db.query(Notification).filter(
                Notification.user_id == student.id,
                Notification.type    == "session_cancelled",
                Notification.message.contains(str(session.id)[:8]),
            ).first()
            if not already_notified:
                db.add(Notification(
                    user_id=student.id,
                    type="session_cancelled",
                    message=(
                        f"Session cancelled: {course_name} on {session.date} "
                        f"({start_str}–{end_str}, Room {session.room})."
                        + (f" Reason: {session.cancellation_reason}" if session.cancellation_reason else "")
                    ),
                    status="pending",
                ))

            # Email
            recipient = student.notification_email
            if recipient:
                try:
                    from app.services.mail_service import send_session_cancellation
                    send_session_cancellation(
                        to=recipient,
                        full_name=student.full_name,
                        course=course_name,
                        date=str(session.date),
                        start_time=start_str,
                        end_time=end_str,
                        room=session.room,
                        reason=session.cancellation_reason,
                    )
                except Exception as e:
                    email_errors += 1
                    logger.warning(f"[OpenClaw] Cancellation email failed for {student.email}: {e}")

        # Mark as processed (idempotency record)
        db.add(FollowUpTask(
            session_id=session.id,
            task_type="cancellation_followup",
            title=f"Cancellation processed — {course_name} {session.date}",
            description=f"{len(students)} students notified. Email errors: {email_errors}.",
            status="done",
        ))

        processed += 1
        logger.info(
            f"[OpenClaw] Cancellation dispatched: session={session.id} "
            f"course={course_name} date={session.date} students={len(students)}"
        )

    db.commit()
    return {"message": f"{processed} cancellation(s) processed", "processed": processed}
