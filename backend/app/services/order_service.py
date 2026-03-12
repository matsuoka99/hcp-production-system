from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.order import Order
from app.models.client import Client
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate


def create_order(db: Session, order_data: OrderCreate) -> Order:
    client = db.get(Client, order_data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    product = db.get(Product, order_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    user = db.get(User, order_data.created_by_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário criador não encontrado.")

    order = Order(
        name=order_data.name,
        client_id=order_data.client_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        completed_quantity=0,
        created_by_user_id=order_data.created_by_user_id,
        description=order_data.description,
        delivery_date=order_data.delivery_date,
        is_active=True,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def list_orders(db: Session) -> list[Order]:
    orders = db.execute(select(Order).order_by(Order.id)).scalars().all()
    return orders