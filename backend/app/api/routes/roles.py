from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role_service import (
    create_role,
    get_role_by_id,
    get_roles,
    update_role,
)


router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
def get_roles_route(db: Session = Depends(get_db)):
    return get_roles(db)


@router.get("/{role_id}", response_model=RoleRead)
def get_role_by_id_route(
    role_id: int,
    db: Session = Depends(get_db),
):
    return get_role_by_id(db, role_id)


@router.post("", response_model=RoleRead)
def create_role_route(
    role_data: RoleCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_role(db, role_data, acting_user_id)


@router.patch("/{role_id}", response_model=RoleRead)
def update_role_route(
    role_id: int,
    role_data: RoleUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_role(db, role_id, role_data, acting_user_id)