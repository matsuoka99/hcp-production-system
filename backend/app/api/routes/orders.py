from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import create_order, list_orders

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead)
def create_order_endpoint(order_data: OrderCreate, db: Session = Depends(get_db)):
    return create_order(db, order_data)


@router.get("", response_model=list[OrderRead])
def list_orders_endpoint(db: Session = Depends(get_db)):
    return list_orders(db)