from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.kit import Kit
from app.models.product import Product
from app.models.order_kit import OrderKit
from app.schemas.kit import KitCreate, KitUpdate
from app.utils.patch import apply_patch
from app.utils.permissions import require_minimum_role


def get_kits(
    db: Session,
    is_active: bool | None = None,
    is_complete: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = (
        select(Kit)
        .join(Product, Kit.product_id == Product.id)
        .options(joinedload(Kit.product))
    )

    if is_active is not None:
        stmt = stmt.where(Kit.is_active == is_active)

    if is_complete is not None:
        stmt = stmt.where(Kit.is_complete == is_complete)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Kit.name.ilike(pattern),
                Kit.description.ilike(pattern),
                Product.name.ilike(pattern),
                Product.hcp_code.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Kit.id).limit(limit).offset(offset)

    return db.execute(stmt).scalars().all()


def get_kit_by_id(db: Session, kit_id: int):
    kit = db.get(Kit, kit_id)

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit não encontrado.",
        )

    return kit


def create_kit(
    db: Session,
    data: KitCreate,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    existing_kit = db.execute(
        select(Kit).where(Kit.name == data.name)
    ).scalar_one_or_none()

    if existing_kit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um kit com esse nome.",
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quantidade deve ser maior que zero.",
        )

    kit = Kit(
        name=data.name,
        product_id=data.product_id,
        quantity=data.quantity,
        remaining_quantity=data.quantity,
        description=data.description,
        is_complete=data.is_complete,
        created_by_user_id=acting_user_id,
        is_active=True,
        closed_at=None,
        closed_by_user_id=None,
    )

    db.add(kit)
    db.commit()
    db.refresh(kit)

    return kit


def update_kit(
    db: Session,
    kit_id: int,
    data: KitUpdate,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    kit = db.get(Kit, kit_id)

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit não encontrado.",
        )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização.",
        )

    is_active_was_sent = "is_active" in update_data
    new_is_active = update_data.get("is_active")

    apply_patch(kit, update_data)

    if is_active_was_sent:
        if new_is_active is False:
            kit.closed_at = datetime.utcnow()
            kit.closed_by_user_id = acting_user_id
        elif new_is_active is True:
            kit.closed_at = None
            kit.closed_by_user_id = None

    db.commit()
    db.refresh(kit)

    return kit


def delete_kit(
    db: Session,
    kit_id: int,
    acting_user_id: int,
):
    require_minimum_role(db, acting_user_id, "supervisor")

    kit = db.get(Kit, kit_id)
    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit não encontrado.",
        )

    if not kit.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kit já está inativo.",
        )

    order_kits = (
        db.query(OrderKit)
        .options(joinedload(OrderKit.order))
        .filter(OrderKit.kit_id == kit.id)
        .all()
    )

    # Não permite excluir kit vinculado a pedido já finalizado/inativo.
    for order_kit in order_kits:
        if not order_kit.order.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível excluir um kit vinculado a pedido finalizado.",
            )

    for order_kit in order_kits:
        db.delete(order_kit)

    kit.is_active = False
    kit.closed_at = datetime.utcnow()
    kit.closed_by_user_id = acting_user_id

    db.commit()
    db.refresh(kit)

    return kit

def get_orders_by_kit(
    db: Session,
    kit_id: int,
):
    """
    Retorna todas as orders associadas a um kit específico.

    Regras:
    - retorna a quantidade alocada de cada vínculo
    - inclui se o pedido está ativo ou não
    """

    kit = db.get(Kit, kit_id)
    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit não encontrado.",
        )

    order_kits = (
        db.query(OrderKit)
        .options(joinedload(OrderKit.order))
        .filter(OrderKit.kit_id == kit.id)
        .order_by(OrderKit.id.asc())
        .all()
    )

    return {
        "kit_id": kit.id,
        "kit_name": kit.name,
        "orders": [
            {
                "order_id": order_kit.order.id,
                "order_name": order_kit.order.name,
                "allocated_quantity": order_kit.allocated_quantity,
                "order_is_active": order_kit.order.is_active,
            }
            for order_kit in order_kits
        ],
    }