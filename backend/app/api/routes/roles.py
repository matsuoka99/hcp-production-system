from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role_service import (
    create_role,
    list_roles,
    get_role_by_id,
    update_role,
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", response_model=RoleRead)
def create_role_endpoint(
    role_data: RoleCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_role(db, role_data, acting_user_id)


@router.get("", response_model=list[RoleRead])
def list_roles_endpoint(db: Session = Depends(get_db)):
    return list_roles(db)


@router.get("/{role_id}", response_model=RoleRead)
def get_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
):
    return get_role_by_id(db, role_id)


@router.patch("/{role_id}", response_model=RoleRead)
def update_role_endpoint(
    role_id: int,
    role_data: RoleUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_role(db, role_id, role_data, acting_user_id)