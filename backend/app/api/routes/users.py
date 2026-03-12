from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_id,
    get_users,
    update_user,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user_route(
    user_data: UserCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_user(db, user_data, acting_user_id)


@router.get("", response_model=list[UserRead])
def get_users_route(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_users(db, is_active=is_active)


@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id_route(
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user_route(
    user_id: int,
    user_data: UserUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_user(db, user_id, user_data, acting_user_id)


@router.delete("/{user_id}", response_model=UserRead)
def delete_user_route(
    user_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return delete_user(db, user_id, acting_user_id)