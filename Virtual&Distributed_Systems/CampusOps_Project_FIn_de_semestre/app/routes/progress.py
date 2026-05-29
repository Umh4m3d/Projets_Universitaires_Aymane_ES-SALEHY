"""
Progress Tracking routes.

POST   /api/v1/progress/          → log a progress entry    (teacher, admin, secretary)
GET    /api/v1/progress/           → list entries           (admin, secretary, teacher)
GET    /api/v1/progress/summary    → % completion by group  (admin, secretary, teacher)
PATCH  /api/v1/progress/{id}       → update an entry        (teacher, admin, secretary)
DELETE /api/v1/progress/{id}       → delete an entry        (admin)
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.progress import ProgressEntry
from app.models.course import Course
from app.models.group import Group
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["Progress"])

VALID_TYPES = {"chapter", "competency", "tp"}


class ProgressCreate(BaseModel):
    course_id:  UUID
    group_id:   UUID
    chapter:    str
    entry_type: str = Field(..., description="chapter | competency | tp")
    completion: float = Field(0.0, ge=0.0, le=100.0)
    notes:      Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "course_id":  "...",
                "group_id":   "...",
                "chapter":    "Chapter 3: Integrals",
                "entry_type": "chapter",
                "completion": 75.0,
                "notes":      "Covered sections 3.1–3.4",
            }
        }


class ProgressUpdate(BaseModel):
    chapter:    Optional[str] = None
    completion: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes:      Optional[str] = None


class ProgressOut(BaseModel):
    id:          UUID
    course_id:   UUID
    group_id:    UUID
    teacher_id:  UUID
    chapter:     str
    entry_type:  str
    completion:  float
    notes:       Optional[str]
    created_at:  datetime
    updated_at:  datetime
    course_name: str
    group_name:  str
    teacher_name: str

    model_config = {"from_attributes": True}


def enrich(entry: ProgressEntry, db: DBSession) -> dict:
    course  = db.query(Course).filter(Course.id == entry.course_id).first()
    group   = db.query(Group).filter(Group.id == entry.group_id).first()
    teacher = db.query(User).filter(User.id == entry.teacher_id).first()
    return {
        "id":           str(entry.id),
        "course_id":    str(entry.course_id),
        "group_id":     str(entry.group_id),
        "teacher_id":   str(entry.teacher_id),
        "chapter":      entry.chapter,
        "entry_type":   entry.entry_type,
        "completion":   entry.completion,
        "notes":        entry.notes,
        "created_at":   str(entry.created_at),
        "updated_at":   str(entry.updated_at),
        "course_name":  course.name       if course  else "Unknown",
        "group_name":   group.name        if group   else "Unknown",
        "teacher_name": teacher.full_name if teacher else "Unknown",
    }


@router.post("/", status_code=201)
def create_entry(
    data: ProgressCreate,
    current_user: User = Depends(require_role("teacher", "admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    if data.entry_type not in VALID_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"entry_type must be one of: {', '.join(VALID_TYPES)}"
        )
    if not db.query(Course).filter(Course.id == data.course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")
    if not db.query(Group).filter(Group.id == data.group_id).first():
        raise HTTPException(status_code=404, detail="Group not found")

    entry = ProgressEntry(
        course_id=data.course_id,
        group_id=data.group_id,
        teacher_id=current_user.id,
        chapter=data.chapter.strip(),
        entry_type=data.entry_type,
        completion=round(data.completion, 1),
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return enrich(entry, db)


@router.get("/")
def list_entries(
    course_id:  Optional[UUID] = Query(None),
    group_id:   Optional[UUID] = Query(None),
    entry_type: Optional[str]  = Query(None),
    current_user: User = Depends(require_role("admin", "secretary", "teacher", "student")),
    db: DBSession = Depends(get_db),
):
    query = db.query(ProgressEntry)
    # Students can only see progress for their own group
    if current_user.role == "student":
        from app.models.student_profile import StudentProfile
        profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        if profile and profile.group_id:
            query = query.filter(ProgressEntry.group_id == profile.group_id)
        else:
            return []  # student has no group assigned
    if course_id:
        query = query.filter(ProgressEntry.course_id == course_id)
    if group_id:
        query = query.filter(ProgressEntry.group_id == group_id)
    if entry_type:
        query = query.filter(ProgressEntry.entry_type == entry_type)
    entries = query.order_by(ProgressEntry.updated_at.desc()).all()
    return [enrich(e, db) for e in entries]


@router.get("/summary")
def progress_summary(
    course_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_role("admin", "secretary", "teacher", "student")),
    db: DBSession = Depends(get_db),
):
    query = db.query(ProgressEntry)
    if current_user.role == "student":
        from app.models.student_profile import StudentProfile
        profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        if profile and profile.group_id:
            query = query.filter(ProgressEntry.group_id == profile.group_id)
        else:
            return []
    if course_id:
        query = query.filter(ProgressEntry.course_id == course_id)
    entries = query.all()
 
    buckets: dict[tuple, list[float]] = {}
    for e in entries:
        key = (str(e.course_id), str(e.group_id))
        buckets.setdefault(key, []).append(e.completion)
 
    summary = []
    for (cid, gid), completions in buckets.items():
        course = db.query(Course).filter(Course.id == cid).first()
        group  = db.query(Group).filter(Group.id == gid).first()
        avg    = round(sum(completions) / len(completions), 1)
        summary.append({
            "course_id":      cid,
            "group_id":       gid,
            "course_name":    course.name if course else "Unknown",
            "group_name":     group.name  if group  else "Unknown",
            "avg_completion": avg,
            "entry_count":    len(completions),
        })
 
    summary.sort(key=lambda x: x["course_name"])
    return summary
 

@router.patch("/{entry_id}")
def update_entry(
    entry_id: UUID,
    data: ProgressUpdate,
    current_user: User = Depends(require_role("teacher", "admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    entry = db.query(ProgressEntry).filter(ProgressEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Progress entry not found")

    # Teachers can only edit their own entries
    if current_user.role == "teacher" and entry.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own entries")

    if data.chapter is not None:
        entry.chapter = data.chapter.strip()
    if data.completion is not None:
        entry.completion = round(data.completion, 1)
    if data.notes is not None:
        entry.notes = data.notes.strip() or None

    db.commit()
    db.refresh(entry)
    return enrich(entry, db)


@router.delete("/{entry_id}", status_code=200)
def delete_entry(
    entry_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    entry = db.query(ProgressEntry).filter(ProgressEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Progress entry not found")
    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted"}
