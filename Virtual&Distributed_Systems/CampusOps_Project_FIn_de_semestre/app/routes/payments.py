from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.services.payment_service import (
    create_payment, record_payment,
    get_student_payments, get_all_payments,
    check_overdue_payments
)

router = APIRouter(prefix="/payments", tags=["Payments"])


def enrich_payments(payments: list, db: DBSession) -> list[dict]:
    """Add student_name to each payment for admin/secretary views."""
    result = []
    for p in payments:
        student = db.query(User).filter(User.id == p.student_id).first()
        result.append({
            "id":             str(p.id),
            "student_id":     str(p.student_id),
            "created_by_id":  str(p.created_by_id),
            "amount":         p.amount,
            "amount_paid":    p.amount_paid,
            "type":           p.type,
            "month":          p.month,
            "due_date":       str(p.due_date),
            "status":         p.status,
            "notes":          p.notes,
            "created_at":     str(p.created_at),
            "student_name":   student.full_name if student else "Unknown",
        })
    return result


@router.post("/", response_model=PaymentOut, status_code=201)
def create(
    data: PaymentCreate,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    return create_payment(db, data, created_by=current_user)


@router.get("/mine", response_model=list[PaymentOut])
def my_payments(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return get_student_payments(db, current_user.id)


@router.get("/")
def list_payments(
    status: Optional[str] = Query(None),
    student_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    payments = get_all_payments(db, status=status, student_id=student_id)
    return enrich_payments(payments, db)


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: UUID,
    data: PaymentUpdate,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    return record_payment(db, payment_id, data, updated_by=current_user)


@router.post("/check-overdue", status_code=200)
def trigger_overdue_check(
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    count = check_overdue_payments(db)
    return {
        "message": f"Overdue check complete. {count} payments marked overdue."
    }
