from uuid import UUID
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class PaymentCreate(BaseModel):
    student_id: UUID
    amount: float
    type: str
    month: Optional[str] = None
    due_date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return round(v, 2)

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in ("registration", "monthly"):
            raise ValueError("Type must be 'registration' or 'monthly'")
        return v

    @field_validator("month")
    @classmethod
    def valid_month_format(cls, v):
        if v is None:
            return v
        import re
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Month must be in format YYYY-MM")
        return v


class PaymentUpdate(BaseModel):
    amount_paid: float
    notes: Optional[str] = None

    @field_validator("amount_paid")
    @classmethod
    def amount_paid_positive(cls, v):
        if v < 0:
            raise ValueError("Amount paid cannot be negative")
        return round(v, 2)


class PaymentOut(BaseModel):
    id: UUID
    student_id: UUID
    created_by_id: UUID
    amount: float
    amount_paid: float
    type: str
    month: Optional[str]
    due_date: date
    status: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
