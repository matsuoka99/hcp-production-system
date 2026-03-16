from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.kit import KitCreate, KitRead, KitUpdate
from app.services.kit_service import (
    create_kit,
    delete_kit,
    get_kit_by_id,
    get_kits,
    update_kit,
)

router = APIRouter(prefix="/kits", tags=["kits"])


@router.get("", response_model=list[KitRead])
def get_kits_route(
    is_active: bool | None = Query(default=None),
    is_complete: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return get_kits(
        db,
        is_active=is_active,
        is_complete=is_complete,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=KitRead)
def create_kit_route(
    data: KitCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_kit(db, data, acting_user_id)


@router.get("/{kit_id}", response_model=KitRead)
def get_kit_by_id_route(
    kit_id: int,
    db: Session = Depends(get_db),
):
    return get_kit_by_id(db, kit_id)


@router.patch("/{kit_id}", response_model=KitRead)
def update_kit_route(
    kit_id: int,
    data: KitUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_kit(db, kit_id, data, acting_user_id)


@router.delete("/{kit_id}", response_model=KitRead)
def delete_kit_route(
    kit_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return delete_kit(db, kit_id, acting_user_id)