import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    notification_email = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    role = Column(
        SAEnum("admin", "secretary", "teacher", "student", name="user_role"),
        nullable=False,
        default="student"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Telegram integration
    telegram_chat_id = Column(String(50), nullable=True, unique=True)
    telegram_otp = Column(String(6), nullable=True)
    telegram_otp_expires = Column(DateTime(timezone=True), nullable=True)

    # Password reset
    reset_token = Column(String(100), nullable=True, unique=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
