from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, EmailStr

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.models.group import Group

router = APIRouter(prefix="/students", tags=["Students"])


class StudentProfileCreate(BaseModel):
    user_id:       UUID
    establishment: str
    group_id:      Optional[UUID] = None
    year:          int
    parent_email:  Optional[EmailStr] = None


class StudentProfileUpdate(BaseModel):
    establishment: Optional[str]      = None
    group_id:      Optional[UUID]     = None
    year:          Optional[int]      = None
    parent_email:  Optional[EmailStr] = None   # allow explicit null to clear it


class StudentProfileOut(BaseModel):
    id:            UUID
    user_id:       UUID
    establishment: str
    group_id:      Optional[UUID]
    group_name:    Optional[str]
    year:          int
    full_name:     str
    email:         str
    parent_email:  Optional[str]

    model_config = {"from_attributes": True}


def enrich_profile(profile: StudentProfile, db: DBSession) -> dict:
    group = db.query(Group).filter(
        Group.id == profile.group_id
    ).first() if profile.group_id else None
    return {
        "id":            str(profile.id),
        "user_id":       str(profile.user_id),
        "establishment": profile.establishment,
        "group_id":      str(profile.group_id) if profile.group_id else None,
        "group_name":    group.name if group else None,
        "year":          profile.year,
        "full_name":     profile.user.full_name,
        "email":         profile.user.email,
        "parent_email":  profile.parent_email,
    }


@router.post("/", status_code=201)
def create_profile(
    data: StudentProfileCreate,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    student = db.query(User).filter(
        User.id == data.user_id,
        User.role == "student",
        User.is_active == True,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = db.query(StudentProfile).filter(
        StudentProfile.user_id == data.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists for this student")

    profile = StudentProfile(
        user_id=data.user_id,
        establishment=data.establishment.strip(),
        group_id=data.group_id,
        year=data.year,
        parent_email=str(data.parent_email).lower() if data.parent_email else None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return enrich_profile(profile, db)


@router.get("/")
def list_profiles(
    group_id:      Optional[UUID] = None,
    establishment: Optional[str]  = None,
    year:          Optional[int]  = None,
    current_user: User = Depends(require_role("admin", "secretary", "teacher")),
    db: DBSession = Depends(get_db),
):
    query = db.query(StudentProfile)
    if group_id:
        query = query.filter(StudentProfile.group_id == group_id)
    if establishment:
        query = query.filter(StudentProfile.establishment.ilike(f"%{establishment}%"))
    if year:
        query = query.filter(StudentProfile.year == year)
    return [enrich_profile(p, db) for p in query.all()]


@router.get("/by-user/{user_id}")
def get_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Students can only view their own profile")

    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == user_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return enrich_profile(profile, db)


@router.patch("/{profile_id}")
def update_profile(
    profile_id: UUID,
    data: StudentProfileUpdate,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(
        StudentProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if data.establishment is not None:
        profile.establishment = data.establishment.strip()
    if "group_id" in data.model_fields_set:
        profile.group_id = data.group_id
    if data.year is not None:
        profile.year = data.year
    if "parent_email" in data.model_fields_set:
        profile.parent_email = (
            str(data.parent_email).lower() if data.parent_email else None
        )

    db.commit()
    db.refresh(profile)
    return enrich_profile(profile, db)


@router.patch("/{profile_id}/clear-parent-email", status_code=200)
def clear_parent_email(
    profile_id: UUID,
    current_user: User = Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    """Dedicated endpoint to remove the parent email."""
    profile = db.query(StudentProfile).filter(
        StudentProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.parent_email = None
    db.commit()
    return {"message": "Parent email cleared"}
