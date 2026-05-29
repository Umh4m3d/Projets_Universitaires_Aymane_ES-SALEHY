import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Absence(Base):
    __tablename__ = "absences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    marked_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_justified = Column(Boolean, default=False, nullable=False)
    justification = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", foreign_keys=[session_id])
    student = relationship("User", foreign_keys=[student_id])
    marked_by = relationship("User", foreign_keys=[marked_by_id])
