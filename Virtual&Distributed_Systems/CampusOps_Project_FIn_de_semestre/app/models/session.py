# /models/session.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Time, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id        = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"),   nullable=False)
    group_id         = Column(UUID(as_uuid=True), ForeignKey("groups.id"),  nullable=False)
    room             = Column(String(50),  nullable=False)
    date             = Column(Date,        nullable=False)
    start_time       = Column(Time,        nullable=False)
    end_time         = Column(Time,        nullable=False)

    # Allowed statuses: pending | approved | rejected | cancelled
    status           = Column(String(20),  default="approved", nullable=False)

    submitted_by_id  = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    # ← NEW: populated when a teacher or admin cancels an approved session
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_by_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cancelled_at        = Column(DateTime(timezone=True), nullable=True)

    created_at       = Column(DateTime(timezone=True),
                              default=lambda: datetime.now(timezone.utc))

    course       = relationship("Course", back_populates="sessions")
    teacher      = relationship("User", foreign_keys=[teacher_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    group        = relationship("Group", back_populates="sessions")
