from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.client_product import ClientProduct
from app.models.order import Order
from app.models.order_kit import OrderKit
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate
from app.utils.patch import apply_patch
from app.utils.permissions import require_minimum_role


def _build_order_response(
    order: Order,
    allocated_quantity_total: int,
) -> dict:
    """
    Monta o payload padrão de resposta de pedidos,
    incluindo campos derivados de alocação e finalização.
    """
    remaining_to_allocate = order.quantity - allocated_quantity_total

    return {
        "id": order.id,
        "name": order.name,
        "client_id": order.client_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "completed_quantity": order.completed_quantity,
        "created_by_user_id": order.created_by_user_id,
        "description": order.description,
        "delivery_date": order.delivery_date,
        "is_active": order.is_active,
        "allocated_quantity_total": int(allocated_quantity_total or 0),
        "remaining_to_allocate": int(remaining_to_allocate or 0),
        "is_fully_allocated": (remaining_to_allocate or 0) <= 0,
        "created_at": order.created_at,
        "closed_at": order.closed_at,
        "closed_by_user_id": order.closed_by_user_id,
        "is_ready_to_finalize": order.is_active and order.completed_quantity >= order.quantity,
    }


def _get_allocated_quantity_total(db: Session, order_id: int) -> int:
    """
    Retorna a quantidade total alocada em kits para um pedido.
    """
    total = db.execute(
        select(func.coalesce(func.sum(OrderKit.allocated_quantity), 0)).where(
            OrderKit.order_id == order_id
        )
    ).scalar_one()

    return int(total or 0)


def get_orders(
    db: Session,
    is_active: bool | None = None,
    search: str | None = None,
    allocation_status: str | None = None,
    ready_to_finalize: bool | None = None,
    limit: int = 50,
    offset: int = 0,
):
    allocated_total_expr = func.coalesce(func.sum(OrderKit.allocated_quantity), 0)
    remaining_expr = Order.quantity - allocated_total_expr

    stmt = (
        select(
            Order,
            allocated_total_expr.label("allocated_quantity_total"),
            remaining_expr.label("remaining_to_allocate"),
        )
        .join(Client, Order.client_id == Client.id)
        .join(Product, Order.product_id == Product.id)
        .outerjoin(OrderKit, Order.id == OrderKit.order_id)
        .group_by(Order.id)
    )

    if is_active is not None:
        stmt = stmt.where(Order.is_active == is_active)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Order.name.ilike(pattern),
                Order.description.ilike(pattern),
                Client.name.ilike(pattern),
                Product.name.ilike(pattern),
                Product.hcp_code.ilike(pattern),
            )
        )

    if allocation_status == "pending":
        stmt = stmt.having(remaining_expr > 0)
    elif allocation_status == "complete":
        stmt = stmt.having(remaining_expr <= 0)
    elif allocation_status is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allocation_status deve ser 'pending' ou 'complete'.",
        )

    if ready_to_finalize is True:
        stmt = stmt.having(
            Order.is_active.is_(True),
            Order.completed_quantity >= Order.quantity,
        )
    elif ready_to_finalize is False:
        stmt = stmt.having(
            or_(
                Order.is_active.is_(False),
                Order.completed_quantity < Order.quantity,
            )
        )

    stmt = stmt.order_by(Order.id).limit(limit).offset(offset)

    rows = db.execute(stmt).all()

    result = []
    for order, allocated_quantity_total, _remaining_to_allocate in rows:
        result.append(
            _build_order_response(
                order=order,
                allocated_quantity_total=int(allocated_quantity_total or 0),
            )
        )

    return result


def get_order_by_id(db: Session, order_id: int):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    allocated_total = _get_allocated_quantity_total(db, order_id)

    return _build_order_response(
        order=order,
        allocated_quantity_total=allocated_total,
    )


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

    # Garante o relacionamento client_products para consultas rápidas.
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

    return _build_order_response(
        order=order,
        allocated_quantity_total=0,
    )


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

    allocated_total = _get_allocated_quantity_total(db, order.id)

    return _build_order_response(
        order=order,
        allocated_quantity_total=allocated_total,
    )


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

    allocated_total = _get_allocated_quantity_total(db, order.id)

    return _build_order_response(
        order=order,
        allocated_quantity_total=allocated_total,
    )


def finalize_order(
    db: Session,
    order_id: int,
    acting_user_id: int,
):
    """
    Finaliza explicitamente um pedido.
    Esta operação não é automática: depende de ação do usuário.
    """
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
            detail="O pedido já está finalizado.",
        )

    if order.completed_quantity < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O pedido ainda não está pronto para finalização.",
        )

    order.is_active = False
    order.closed_at = datetime.utcnow()
    order.closed_by_user_id = acting_user_id

    db.commit()
    db.refresh(order)

    allocated_total = _get_allocated_quantity_total(db, order.id)

    return _build_order_response(
        order=order,
        allocated_quantity_total=allocated_total,
    )