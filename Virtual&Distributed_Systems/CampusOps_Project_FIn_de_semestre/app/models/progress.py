"""
Progress tracking model.

Tracks chapter/competency/TP completion per course per group.
Teachers update progress; admins and secretaries can view reports.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProgressEntry(Base):
    __tablename__ = "progress_entries"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id   = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    group_id    = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    teacher_id  = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # What was covered
    chapter     = Column(String(255), nullable=False)       # e.g. "Chapter 3: Integrals"
    entry_type  = Column(String(50),  nullable=False)       # "chapter" | "competency" | "tp"
    notes       = Column(Text, nullable=True)

    # Completion percentage for this item (0–100)
    completion  = Column(Float, default=0.0, nullable=False)

    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    course  = relationship("Course", foreign_keys=[course_id])
    group   = relationship("Group",  foreign_keys=[group_id])
    teacher = relationship("User",   foreign_keys=[teacher_id])
