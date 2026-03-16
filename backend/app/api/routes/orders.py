from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services.order_service import (
    create_order,
    delete_order,
    finalize_order,
    get_order_by_id,
    get_orders,
    update_order,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def get_orders_route(
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    allocation_status: str | None = Query(default=None),
    ready_to_finalize: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return get_orders(
        db,
        is_active=is_active,
        search=search,
        allocation_status=allocation_status,
        ready_to_finalize=ready_to_finalize,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=OrderRead)
def create_order_route(
    data: OrderCreate,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return create_order(db, data, acting_user_id)


@router.get("/{order_id}", response_model=OrderRead)
def get_order_by_id_route(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_order_by_id(db, order_id)


@router.patch("/{order_id}", response_model=OrderRead)
def update_order_route(
    order_id: int,
    data: OrderUpdate,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return update_order(db, order_id, data, acting_user_id)


@router.delete("/{order_id}", response_model=OrderRead)
def delete_order_route(
    order_id: int,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return delete_order(db, order_id, acting_user_id)


@router.post("/{order_id}/finalize", response_model=OrderRead)
def finalize_order_route(
    order_id: int,
    acting_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Finaliza explicitamente um pedido que já atingiu
    a quantidade concluída necessária.
    """
    return finalize_order(db, order_id, acting_user_id)