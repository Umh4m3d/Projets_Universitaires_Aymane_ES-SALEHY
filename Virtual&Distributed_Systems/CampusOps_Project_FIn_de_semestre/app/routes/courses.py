from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from uuid import UUID
from pydantic import BaseModel
from app.core.dependencies import require_role, get_current_user
from app.db.session import get_db
from app.models.course import Course

router = APIRouter(prefix="/courses", tags=["Courses"])


class CourseCreate(BaseModel):
    name: str
    description: str = ""


class CourseOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_config = {"from_attributes": True}


@router.post("/", response_model=CourseOut, status_code=201)
def create_course(
    data: CourseCreate,
    current_user=Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    course = Course(name=data.name.strip(), description=data.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/", response_model=list[CourseOut])
def list_courses(
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return db.query(Course).all()
