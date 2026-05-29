from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session as DBSession
from uuid import UUID
from pydantic import BaseModel
from app.core.dependencies import require_role, get_current_user
from app.db.session import get_db
from app.models.group import Group

router = APIRouter(prefix="/groups", tags=["Groups"])


class GroupCreate(BaseModel):
    name: str
    description: str = ""


class GroupOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_config = {"from_attributes": True}


@router.post("/", response_model=GroupOut, status_code=201)
def create_group(
    data: GroupCreate,
    current_user=Depends(require_role("admin", "secretary")),
    db: DBSession = Depends(get_db),
):
    group = Group(name=data.name.strip(), description=data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("/", response_model=list[GroupOut])
def list_groups(
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return db.query(Group).all()
