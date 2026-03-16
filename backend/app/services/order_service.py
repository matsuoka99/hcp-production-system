from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.models.order import Order
from app.models.client import Client
from app.models.product import Product
from app.models.client_product import ClientProduct
from app.schemas.order import OrderCreate, OrderUpdate
from app.utils.permissions import require_minimum_role
from app.utils.patch import apply_patch


def get_orders(
    db: Session,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = (
        select(Order)
        .options(joinedload(Order.client), joinedload(Order.product))
    )

    if is_active is not None:
        stmt = stmt.where(Order.is_active == is_active)

    if search:
        stmt = stmt.where(
            or_(
                Order.name.ilike(f"%{search}%"),
                Order.description.ilike(f"%{search}%") if Order.description is not None else False,
                Client.name.ilike(f"%{search}%"),
                Product.name.ilike(f"%{search}%"),
                Product.hcp_code.ilike(f"%{search}%"),
            )
        ).join(Client).join(Product)

    stmt = stmt.order_by(Order.id).limit(limit).offset(offset)

    return db.execute(stmt).scalars().all()


def get_order_by_id(db: Session, order_id: int):
    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    return order


def create_order(
    db: Session,
    data: OrderCreate,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    client = db.get(Client, data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    existing_order = db.execute(
        select(Order).where(Order.name == data.name)
    ).scalar_one_or_none()

    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um pedido com esse nome.",
        )

    order = Order(
    name=data.name,
    client_id=data.client_id,
    product_id=data.product_id,
    quantity=data.quantity,
    completed_quantity=0,
    delivery_date=data.delivery_date,
    description=data.description,
    created_by_user_id=acting_user_id,
    is_active=True,
    )

    db.add(order)

    # garante vínculo em client_products
    existing_link = db.execute(
        select(ClientProduct).where(
            ClientProduct.client_id == data.client_id,
            ClientProduct.product_id == data.product_id,
        )
    ).scalar_one_or_none()

    if not existing_link:
        link = ClientProduct(
            client_id=data.client_id,
            product_id=data.product_id,
        )
        db.add(link)

    db.commit()
    db.refresh(order)

    return order


def update_order(
    db: Session,
    order_id: int,
    data: OrderUpdate,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização.",
        )

    apply_patch(order, update_data)

    db.commit()
    db.refresh(order)

    return order


def delete_order(
    db: Session,
    order_id: int,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedido já está inativo.",
        )

    order.is_active = False

    db.commit()
    db.refresh(order)

    return order