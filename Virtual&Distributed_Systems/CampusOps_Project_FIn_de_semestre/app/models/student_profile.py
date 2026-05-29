import uuid
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    establishment = Column(String(150), nullable=False)
    group_id      = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    year          = Column(Integer, nullable=False)
    parent_email  = Column(String(255), nullable=True)   # ← new

    user  = relationship("User",  foreign_keys=[user_id])
    group = relationship("Group", foreign_keys=[group_id])
