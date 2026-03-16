from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order_stage_entry import (
    OrderProductionProgressResponse,
    OrderStageEntryCreate,
    OrderStageEntryResponse,
    OrderStageEntryUpdate,
)
from app.services.order_stage_entry_service import (
    create_order_stage_entry,
    delete_order_stage_entry,
    get_order_stage_progress,
    get_order_stage_entry_by_id,
    list_order_stage_entries,
    update_order_stage_entry,
)

router = APIRouter(prefix="/order-stage-entries", tags=["order-stage-entries"])


@router.post("/orders/{order_id}", response_model=OrderStageEntryResponse, status_code=201)
def create_entry(
    order_id: int,
    payload: OrderStageEntryCreate,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return create_order_stage_entry(db, order_id, payload, acting_user_id)


@router.get("/{entry_id}", response_model=OrderStageEntryResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
):
    return get_order_stage_entry_by_id(db, entry_id)


@router.get("", response_model=list[OrderStageEntryResponse])
def list_entries(
    order_id: int | None = Query(default=None, gt=0),
    product_stage_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_order_stage_entries(
        db=db,
        order_id=order_id,
        product_stage_id=product_stage_id,
        limit=limit,
        offset=offset,
    )


@router.patch("/{entry_id}", response_model=OrderStageEntryResponse)
def update_entry(
    entry_id: int,
    payload: OrderStageEntryUpdate,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return update_order_stage_entry(db, entry_id, payload, acting_user_id)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    delete_order_stage_entry(db, entry_id, acting_user_id)
    return None


@router.get("/orders/{order_id}/progress", response_model=OrderProductionProgressResponse)
def get_progress(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_order_stage_progress(db, order_id)