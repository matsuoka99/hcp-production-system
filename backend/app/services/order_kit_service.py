from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.models.kit import Kit
from app.models.order_kit import OrderKit
from app.schemas.order_kit import OrderKitCreate
from app.utils.permissions import require_minimum_role


def _get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    return order


def _get_already_allocated_total(db: Session, order_id: int) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(OrderKit.allocated_quantity), 0)).where(
            OrderKit.order_id == order_id
        )
    ).scalar_one()

    return int(total or 0)


def _build_allocation_summary(
    db: Session,
    order: Order,
    allocations_created: list[dict],
) -> dict:
    allocated_quantity_total = _get_already_allocated_total(db, order.id)
    remaining_to_allocate = order.quantity - allocated_quantity_total
    is_fully_allocated = remaining_to_allocate <= 0

    if is_fully_allocated:
        message = "Alocação concluída com sucesso."
    elif allocations_created:
        message = (
            f"Alocação parcial realizada. Ainda faltam "
            f"{remaining_to_allocate} unidades."
        )
    else:
        message = (
            f"Nenhuma alocação foi realizada. Ainda faltam "
            f"{remaining_to_allocate} unidades."
        )

    return {
        "order_id": order.id,
        "order_name": order.name,
        "order_quantity": order.quantity,
        "allocated_quantity_total": allocated_quantity_total,
        "remaining_to_allocate": remaining_to_allocate,
        "is_fully_allocated": is_fully_allocated,
        "allocations_created": allocations_created,
        "message": message,
    }


def _allocate_single_kit_if_possible(
    db: Session,
    order: Order,
    kit: Kit,
    acting_user_id: int,
) -> dict | None:
    if not kit.is_active or kit.remaining_quantity <= 0:
        return None

    if kit.product_id != order.product_id:
        return None

    existing_link = db.execute(
        select(OrderKit).where(
            OrderKit.order_id == order.id,
            OrderKit.kit_id == kit.id,
        )
    ).scalar_one_or_none()

    if existing_link:
        return None

    already_allocated = _get_already_allocated_total(db, order.id)
    remaining_to_allocate = order.quantity - already_allocated

    if remaining_to_allocate <= 0:
        return None

    allocated_quantity = min(remaining_to_allocate, kit.remaining_quantity)

    if allocated_quantity <= 0:
        return None

    order_kit = OrderKit(
        order_id=order.id,
        kit_id=kit.id,
        allocated_quantity=allocated_quantity,
        allocated_at=datetime.utcnow(),
        allocated_by_user_id=acting_user_id,
    )

    db.add(order_kit)

    kit.remaining_quantity -= allocated_quantity

    if kit.remaining_quantity == 0:
        kit.is_active = False
        kit.closed_at = datetime.utcnow()
        kit.closed_by_user_id = acting_user_id

    db.flush()
    db.refresh(order_kit)

    return {
        "order_kit_id": order_kit.id,
        "kit_id": kit.id,
        "kit_name": kit.name,
        "allocated_quantity": allocated_quantity,
    }



def unlink_order_kit_from_order_delete(order_kit: OrderKit) -> None:
    """
    Desfaz uma alocação quando o cancelamento parte do pedido.

    Regras:
    - devolve a quantidade alocada ao kit
    - reabre o kit se ele voltar a ter saldo disponível
    - remove o vínculo em order_kits
    """
    kit = order_kit.kit

    kit.remaining_quantity += order_kit.allocated_quantity

    # Se o kit voltou a ter saldo disponível, ele pode voltar a ficar ativo.
    if kit.remaining_quantity > 0:
        kit.is_active = True
        kit.closed_at = None
        kit.closed_by_user_id = None



def allocate_kit_to_order(
    db: Session,
    data: OrderKitCreate,
    acting_user_id: int,
) -> OrderKit:
    require_minimum_role(db, acting_user_id, "supervisor")

    order = _get_order_or_404(db, data.order_id)

    if not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível alocar kits para um pedido inativo.",
        )

    kit = db.execute(
        select(Kit)
        .options(joinedload(Kit.product))
        .where(Kit.id == data.kit_id)
    ).scalar_one_or_none()

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit não encontrado.",
        )

    if not kit.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível alocar um kit inativo.",
        )

    if kit.product_id != order.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O kit informado pertence a outro produto.",
        )

    existing_link = db.execute(
        select(OrderKit).where(
            OrderKit.order_id == data.order_id,
            OrderKit.kit_id == data.kit_id,
        )
    ).scalar_one_or_none()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esse kit já está alocado a esse pedido.",
        )

    if kit.remaining_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O kit não possui saldo disponível para alocação.",
        )

    already_allocated = _get_already_allocated_total(db, data.order_id)
    remaining_to_allocate = order.quantity - already_allocated

    if remaining_to_allocate <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O pedido já está totalmente alocado.",
        )

    allocated_quantity = min(remaining_to_allocate, kit.remaining_quantity)

    order_kit = OrderKit(
        order_id=data.order_id,
        kit_id=data.kit_id,
        allocated_quantity=allocated_quantity,
        allocated_at=datetime.utcnow(),
        allocated_by_user_id=acting_user_id,
    )

    db.add(order_kit)

    kit.remaining_quantity -= allocated_quantity

    if kit.remaining_quantity == 0:
        kit.is_active = False
        kit.closed_at = datetime.utcnow()
        kit.closed_by_user_id = acting_user_id

    db.commit()
    db.refresh(order_kit)

    return order_kit


def list_order_kits(db: Session) -> list[OrderKit]:
    return db.execute(
        select(OrderKit)
        .options(
            joinedload(OrderKit.order),
            joinedload(OrderKit.kit).joinedload(Kit.product),
        )
        .order_by(OrderKit.id)
    ).scalars().all()


def get_order_kits_by_order_id(db: Session, order_id: int) -> list[OrderKit]:
    order = _get_order_or_404(db, order_id)

    return db.execute(
        select(OrderKit)
        .options(
            joinedload(OrderKit.order),
            joinedload(OrderKit.kit).joinedload(Kit.product),
        )
        .where(OrderKit.order_id == order_id)
        .order_by(OrderKit.id)
    ).scalars().all()


def get_available_kits_for_order(db: Session, order_id: int) -> list[Kit]:
    order = _get_order_or_404(db, order_id)

    return db.execute(
        select(Kit)
        .options(joinedload(Kit.product))
        .where(
            Kit.product_id == order.product_id,
            Kit.is_active == True,
            Kit.remaining_quantity > 0,
        )
        .order_by(Kit.remaining_quantity.asc(), Kit.id.asc())
    ).scalars().all()


def allocate_selected_kits_to_order(
    db: Session,
    order_id: int,
    kit_ids: list[int],
    acting_user_id: int,
) -> dict:
    require_minimum_role(db, acting_user_id, "supervisor")

    order = _get_order_or_404(db, order_id)

    if not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível alocar kits para um pedido inativo.",
        )

    if not kit_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum kit foi informado para alocação.",
        )

    if len(kit_ids) != len(set(kit_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido repetir kits na mesma solicitação.",
        )

    kits = db.execute(
        select(Kit)
        .options(joinedload(Kit.product))
        .where(Kit.id.in_(kit_ids))
        .order_by(Kit.remaining_quantity.asc(), Kit.id.asc())
    ).scalars().all()

    found_ids = {kit.id for kit in kits}
    missing_ids = [kit_id for kit_id in kit_ids if kit_id not in found_ids]

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kits não encontrados: {missing_ids}.",
        )

    allocations_created: list[dict] = []

    for kit in kits:
        created = _allocate_single_kit_if_possible(db, order, kit, acting_user_id)
        if created:
            allocations_created.append(created)

    db.commit()

    return _build_allocation_summary(db, order, allocations_created)


def auto_allocate_kits_to_order(
    db: Session,
    order_id: int,
    acting_user_id: int,
) -> dict:
    require_minimum_role(db, acting_user_id, "supervisor")

    order = _get_order_or_404(db, order_id)

    if not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível alocar kits para um pedido inativo.",
        )

    kits = db.execute(
        select(Kit)
        .options(joinedload(Kit.product))
        .where(
            Kit.product_id == order.product_id,
            Kit.is_active == True,
            Kit.remaining_quantity > 0,
        )
        .order_by(Kit.remaining_quantity.asc(), Kit.id.asc())
    ).scalars().all()

    allocations_created: list[dict] = []

    for kit in kits:
        created = _allocate_single_kit_if_possible(db, order, kit, acting_user_id)
        if created:
            allocations_created.append(created)

        already_allocated = _get_already_allocated_total(db, order.id)
        if already_allocated >= order.quantity:
            break

    db.commit()

    return _build_allocation_summary(db, order, allocations_created)


def delete_order_kit(
    db: Session,
    order_kit_id: int,
    acting_user_id: int,
) -> OrderKit:
    require_minimum_role(db, acting_user_id, "supervisor")

    order_kit = db.execute(
        select(OrderKit)
        .options(
            joinedload(OrderKit.order),
            joinedload(OrderKit.kit).joinedload(Kit.product),
        )
        .where(OrderKit.id == order_kit_id)
    ).scalar_one_or_none()

    if not order_kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alocação não encontrada.",
        )

    kit = order_kit.kit
    kit.remaining_quantity += order_kit.allocated_quantity

    if not kit.is_active and kit.remaining_quantity > 0:
        kit.is_active = True
        kit.closed_at = None
        kit.closed_by_user_id = None

    db.delete(order_kit)
    db.commit()

    return order_kit