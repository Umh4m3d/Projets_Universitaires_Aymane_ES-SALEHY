import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0, nullable=False)
    type = Column(
        String(50), nullable=False
    )  # "registration" or "monthly"
    month = Column(String(20), nullable=True)  # e.g. "2026-04"
    due_date = Column(Date, nullable=False)
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, partial, paid, overdue
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    student = relationship("User", foreign_keys=[student_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
