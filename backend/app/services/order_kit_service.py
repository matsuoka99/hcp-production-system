from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.order import Order
from app.models.kit import Kit
from app.models.order_kit import OrderKit
from app.models.user import User
from app.schemas.order_kit import OrderKitCreate


def get_available_kits_for_order(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    already_allocated = db.execute(
        select(func.coalesce(func.sum(OrderKit.allocated_quantity), 0)).where(
            OrderKit.order_id == order_id
        )
    ).scalar_one()

    remaining_to_allocate = order.quantity - already_allocated

    kits = db.execute(
        select(Kit)
        .where(
            Kit.product_id == order.product_id,
            Kit.is_active == True,
            Kit.remaining_quantity > 0,
        )
        .order_by(Kit.id)
    ).scalars().all()

    available_kits = [
        {
            "kit_id": kit.id,
            "name": kit.name,
            "remaining_quantity": kit.remaining_quantity,
        }
        for kit in kits
    ]

    total_available = sum(k["remaining_quantity"] for k in available_kits)

    return {
        "order_id": order.id,
        "order_quantity": order.quantity,
        "already_allocated": already_allocated,
        "remaining_to_allocate": remaining_to_allocate,
        "can_fulfill_fully": total_available >= remaining_to_allocate,
        "available_kits": available_kits,
    }


def allocate_kit_to_order(db: Session, data: OrderKitCreate) -> OrderKit:
    order = db.get(Order, data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    kit = db.get(Kit, data.kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Kit não encontrado.")

    user = db.get(User, data.allocated_by_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if not kit.is_active:
        raise HTTPException(status_code=400, detail="O kit está inativo.")

    if kit.product_id != order.product_id:
        raise HTTPException(
            status_code=400,
            detail="O kit não pertence ao mesmo produto do pedido."
        )

    if data.allocated_quantity > kit.remaining_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"O kit não possui saldo suficiente. Saldo disponível: {kit.remaining_quantity}."
        )

    already_allocated = db.execute(
        select(func.coalesce(func.sum(OrderKit.allocated_quantity), 0)).where(
            OrderKit.order_id == data.order_id
        )
    ).scalar_one()

    remaining_to_allocate = order.quantity - already_allocated

    if data.allocated_quantity > remaining_to_allocate:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "A quantidade informada excede o restante necessário do pedido.",
                "remaining_allocatable": remaining_to_allocate,
            }
        )

    existing_allocation = db.execute(
        select(OrderKit).where(
            OrderKit.order_id == data.order_id,
            OrderKit.kit_id == data.kit_id,
        )
    ).scalar_one_or_none()

    if existing_allocation:
        raise HTTPException(
            status_code=400,
            detail="Esse kit já foi alocado para esse pedido."
        )

    allocation = OrderKit(
        order_id=data.order_id,
        kit_id=data.kit_id,
        allocated_quantity=data.allocated_quantity,
        allocated_at=datetime.utcnow(),
        allocated_by_user_id=data.allocated_by_user_id,
    )

    db.add(allocation)

    kit.remaining_quantity -= data.allocated_quantity

    if kit.remaining_quantity == 0:
        kit.is_active = False
        kit.closed_at = datetime.utcnow()
        kit.closed_by_user_id = data.allocated_by_user_id

    db.commit()
    db.refresh(allocation)

    return allocation


def list_order_kits(db: Session) -> list[OrderKit]:
    allocations = db.execute(
        select(OrderKit).order_by(OrderKit.id)
    ).scalars().all()

    return allocations