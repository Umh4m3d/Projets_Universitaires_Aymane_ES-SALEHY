from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class AbsenceCreate(BaseModel):
    session_id: UUID
    student_id: UUID
    justification: Optional[str] = None

    @field_validator("justification")
    @classmethod
    def sanitize_justification(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 500:
            raise ValueError("Justification cannot exceed 500 characters")
        return v


class AbsenceUpdate(BaseModel):
    is_justified: bool
    justification: Optional[str] = None


class AbsenceOut(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    marked_by_id: UUID
    is_justified: bool
    justification: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
