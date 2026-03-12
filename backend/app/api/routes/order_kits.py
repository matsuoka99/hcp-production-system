from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order_kit import (
    OrderKitCreate,
    OrderKitRead,
    OrderAvailableKitsRead,
)
from app.services.order_kit_service import (
    allocate_kit_to_order,
    list_order_kits,
    get_available_kits_for_order,
)

router = APIRouter(prefix="/order-kits", tags=["order-kits"])


@router.post("", response_model=OrderKitRead)
def allocate_kit_to_order_endpoint(
    data: OrderKitCreate,
    db: Session = Depends(get_db),
):
    return allocate_kit_to_order(db, data)


@router.get("", response_model=list[OrderKitRead])
def list_order_kits_endpoint(db: Session = Depends(get_db)):
    return list_order_kits(db)


@router.get("/orders/{order_id}/available-kits", response_model=OrderAvailableKitsRead)
def get_available_kits_for_order_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_available_kits_for_order(db, order_id)