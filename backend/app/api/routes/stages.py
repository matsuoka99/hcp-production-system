from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stage import StageCreate, StageRead, StageUpdate
from app.services.stage_service import (
    create_stage,
    delete_stage,
    get_stage_by_id,
    get_stages,
    update_stage,
)


router = APIRouter(prefix="/stages", tags=["stages"])


@router.post("", response_model=StageRead)
def create_stage_route(
    stage_data: StageCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_stage(db, stage_data, acting_user_id)


@router.get("", response_model=list[StageRead])
def get_stages_route(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_stages(db, is_active=is_active)


@router.patch("/{stage_id}", response_model=StageRead)
def update_stage_route(
    stage_id: int,
    stage_data: StageUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_stage(db, stage_id, stage_data, acting_user_id)


@router.delete("/{stage_id}", response_model=StageRead)
def delete_stage_route(
    stage_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return delete_stage(db, stage_id, acting_user_id)

@router.get("/{stage_id}", response_model=StageRead)
def get_stage_by_id_route(
    stage_id: int,
    db: Session = Depends(get_db),
):
    return get_stage_by_id(db, stage_id)