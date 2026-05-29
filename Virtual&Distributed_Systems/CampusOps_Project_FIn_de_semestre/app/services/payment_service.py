from uuid import UUID
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.logging_config import logger
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentUpdate


def compute_status(amount: float, amount_paid: float, due_date: date) -> str:
    if amount_paid >= amount:
        return "paid"
    if date.today() > due_date:
        return "overdue"
    if amount_paid > 0:
        return "partial"
    return "pending"


def create_payment(db: DBSession, data: PaymentCreate, created_by: User) -> Payment:
    student = db.query(User).filter(
        User.id == data.student_id,
        User.role == "student",
        User.is_active == True,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found or inactive")

    payment = Payment(
        student_id=data.student_id,
        created_by_id=created_by.id,
        amount=data.amount,
        amount_paid=0.0,
        type=data.type,
        month=data.month,
        due_date=data.due_date,
        status="pending",
        notes=data.notes,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def record_payment(
    db: DBSession,
    payment_id: UUID,
    data: PaymentUpdate,
    updated_by: User
) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "paid":
        raise HTTPException(status_code=400, detail="Payment is already fully paid")

    if data.amount_paid > payment.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Amount paid ({data.amount_paid}) cannot exceed "
                   f"total amount ({payment.amount})"
        )

    old_status = payment.status
    payment.amount_paid = data.amount_paid
    payment.status = compute_status(payment.amount, data.amount_paid, payment.due_date)
    if data.notes:
        payment.notes = data.notes

    db.flush()

    if payment.status == "overdue" and old_status != "overdue":
        student = db.query(User).filter(User.id == payment.student_id).first()

        message = (
            f"Payment overdue: {student.full_name} has an unpaid "
            f"{payment.type} fee of {payment.amount} due on {payment.due_date}. "
            f"Please settle your payment as soon as possible."
        )
        notification = Notification(
            user_id=payment.student_id,
            type="payment_overdue",
            message=message,
            status="pending",
        )
        db.add(notification)

        try:
            from app.services.mail_service import send_payment_overdue_notification
            recipient = student.notification_email
            if recipient:
              send_payment_overdue_notification(
                to=recipient,
                full_name=student.full_name,
                amount=payment.amount,
                month=payment.month,
                due_date=str(payment.due_date),)
        except Exception as e:
            logger.warning(f"Could not send overdue payment email: {e}")

        logger.warning(
            f"Payment overdue: student={student.email} "
            f"amount={payment.amount} due={payment.due_date}"
        )

    db.commit()
    db.refresh(payment)
    return payment


def get_student_payments(db: DBSession, student_id: UUID) -> list[Payment]:
    return db.query(Payment).filter(
        Payment.student_id == student_id
    ).order_by(Payment.due_date.desc()).all()


def get_all_payments(
    db: DBSession,
    status: str | None = None,
    student_id: UUID | None = None,
) -> list[Payment]:
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    if student_id:
        query = query.filter(Payment.student_id == student_id)
    return query.order_by(Payment.due_date.desc()).all()


def check_overdue_payments(db: DBSession) -> int:
    today = date.today()
    payments = db.query(Payment).filter(
        Payment.status.in_(["pending", "partial"]),
        Payment.due_date < today,
    ).all()

    count = 0
    for payment in payments:
        payment.status = "overdue"
        db.flush()

        student = db.query(User).filter(User.id == payment.student_id).first()
        if student:
            message = (
                f"Payment overdue: {student.full_name} has an unpaid "
                f"{payment.type} fee of {payment.amount} due on {payment.due_date}."
            )
            db.add(Notification(
                user_id=payment.student_id,
                type="payment_overdue",
                message=message,
                status="pending",
            ))
            # ← FIXED: only send if notification_email is set
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
                    logger.warning(f"Could not send overdue email: {e}")
            else:
                logger.info(f"Skipping overdue email for {student.email} — no notification_email set")

        count += 1

    db.commit()
    return count
