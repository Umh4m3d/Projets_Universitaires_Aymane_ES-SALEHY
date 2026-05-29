from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserRole(str, Enum):
    admin = "admin"
    secretary = "secretary"
    teacher = "teacher"
    student = "student"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.student

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
     if len(v) < 8:
      raise ValueError("Password must be at least 8 characters")
     if len(v) > 64:
      raise ValueError("Password must be 64 characters or less")
     if not any(c.isupper() for c in v):
      raise ValueError("Password must contain at least one uppercase letter")
     if not any(c.isdigit() for c in v):
      raise ValueError("Password must contain at least one number")
     return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty")
        if len(v) > 100:
            raise ValueError("Full name too long")
        return v


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    notification_email: Optional[str] = None   # ← ADD THIS LINE
 
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
