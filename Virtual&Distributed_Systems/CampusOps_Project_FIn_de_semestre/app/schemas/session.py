from uuid import UUID
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class SessionCreate(BaseModel):
    course_id: UUID
    teacher_id: UUID
    group_id: UUID
    room: str
    date: date
    start_time: time
    end_time: time

    @field_validator("room")
    @classmethod
    def room_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Room cannot be empty")
        if len(v) > 50:
            raise ValueError("Room name too long")
        return v

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class SessionOut(BaseModel):
    id: UUID
    course_id: UUID
    teacher_id: UUID
    group_id: UUID
    room: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOutDetailed(BaseModel):
    id: UUID
    room: str
    date: date
    start_time: time
    end_time: time
    course_name: str
    teacher_name: str
    group_name: str

    model_config = {"from_attributes": True}
