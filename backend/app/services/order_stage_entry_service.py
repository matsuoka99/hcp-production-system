from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.order import Order
from app.models.order_stage_entry import OrderStageEntry
from app.models.product_stage import ProductStage
from app.schemas.order_stage_entry import (
    OrderProductionProgressResponse,
    OrderStageEntryCreate,
    OrderStageEntryUpdate,
    OrderStageSummary,
)
from app.utils.patch import apply_patch
from app.utils.permissions import require_minimum_role


def _get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )
    return order


def _get_product_stage_or_404(db: Session, product_stage_id: int) -> ProductStage:
    product_stage = (
        db.query(ProductStage)
        .options(joinedload(ProductStage.stage))
        .filter(ProductStage.id == product_stage_id)
        .first()
    )
    if not product_stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa do produto não encontrada.",
        )
    return product_stage


def _validate_order_is_active(order: Order) -> None:
    if not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível lançar produção em um pedido finalizado.",
        )


def _validate_product_stage_belongs_to_order_product(
    order: Order,
    product_stage: ProductStage,
) -> None:
    if product_stage.product_id != order.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A etapa informada não pertence ao produto deste pedido.",
        )


def _get_last_product_stage_for_order(db: Session, order: Order) -> ProductStage | None:
    return (
        db.query(ProductStage)
        .options(joinedload(ProductStage.stage))
        .filter(ProductStage.product_id == order.product_id)
        .order_by(ProductStage.sequence.desc())
        .first()
    )


def _get_stage_total_for_order(
    db: Session,
    order_id: int,
    product_stage_id: int,
) -> int:
    total = (
        db.query(func.coalesce(func.sum(OrderStageEntry.quantity), 0))
        .filter(
            OrderStageEntry.order_id == order_id,
            OrderStageEntry.product_stage_id == product_stage_id,
        )
        .scalar()
    )
    return int(total or 0)


def _calculate_completed_percent(quantity_completed: int, order_quantity: int) -> float:
    """
    Calcula o percentual concluído em relação à quantidade total do pedido.
    O valor é limitado a 100 para evitar distorções no frontend.
    """
    if order_quantity <= 0:
        return 0.0

    percent = (quantity_completed / order_quantity) * 100
    return round(min(percent, 100.0), 2)


def _calculate_overall_progress_percent(
    stage_quantities: list[int],
    order_quantity: int,
    total_stages: int,
) -> float:
    """
    Calcula o progresso global do pedido considerando a soma das etapas.

    Fórmula:
    soma_das_etapas / (quantidade_do_pedido * número_de_etapas) * 100

    Cada etapa é limitada ao máximo da quantidade do pedido para evitar
    percentuais distorcidos em caso de lançamentos acima do esperado.
    """
    if order_quantity <= 0 or total_stages <= 0:
        return 0.0

    total_capacity = order_quantity * total_stages
    total_done = sum(min(quantity, order_quantity) for quantity in stage_quantities)

    percent = (total_done / total_capacity) * 100
    return round(min(percent, 100.0), 2)


def recalculate_order_completed_quantity(db: Session, order_id: int) -> Order:
    """
    Recalcula orders.completed_quantity com base no total acumulado
    da ÚLTIMA etapa do roteiro do produto.
    """
    order = _get_order_or_404(db, order_id)

    last_product_stage = _get_last_product_stage_for_order(db, order)
    if not last_product_stage:
        # Caso extremo: produto sem roteiro definido.
        order.completed_quantity = 0
        db.commit()
        db.refresh(order)
        return order

    total_last_stage = _get_stage_total_for_order(db, order.id, last_product_stage.id)

    # Evita salvar valor acima da quantidade do pedido.
    order.completed_quantity = min(total_last_stage, order.quantity)

    db.commit()
    db.refresh(order)
    return order


def is_order_ready_to_close(db: Session, order_id: int) -> bool:
    order = _get_order_or_404(db, order_id)
    return order.completed_quantity >= order.quantity


def create_order_stage_entry(
    db: Session,
    order_id: int,
    payload: OrderStageEntryCreate,
    acting_user_id: int,
) -> OrderStageEntry:
    """
    Cria um lançamento de produção para uma etapa do pedido.
    """
    # Exemplo de permissão: supervisor ou superior.
    # Ajuste se quiser permitir operator.
    require_minimum_role(db, acting_user_id, "operator")

    order = _get_order_or_404(db, order_id)
    _validate_order_is_active(order)

    product_stage = _get_product_stage_or_404(db, payload.product_stage_id)
    _validate_product_stage_belongs_to_order_product(order, product_stage)

    entry = OrderStageEntry(
        order_id=order.id,
        product_stage_id=payload.product_stage_id,
        quantity=payload.quantity,
        description=payload.description,
        performed_at=payload.performed_at,
        created_by_user_id=acting_user_id,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Atualiza o resumo persistido do pedido.
    recalculate_order_completed_quantity(db, order.id)

    return entry


def get_order_stage_entry_by_id(db: Session, entry_id: int) -> OrderStageEntry:
    entry = db.get(OrderStageEntry, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lançamento de produção não encontrado.",
        )
    return entry


def list_order_stage_entries(
    db: Session,
    order_id: int | None = None,
    product_stage_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OrderStageEntry]:
    query = db.query(OrderStageEntry)

    if order_id is not None:
        query = query.filter(OrderStageEntry.order_id == order_id)

    if product_stage_id is not None:
        query = query.filter(OrderStageEntry.product_stage_id == product_stage_id)

    return (
        query.order_by(OrderStageEntry.performed_at.desc(), OrderStageEntry.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_order_stage_entry(
    db: Session,
    entry_id: int,
    payload: OrderStageEntryUpdate,
    acting_user_id: int,
) -> OrderStageEntry:
    """
    Permite alteração somente para perfis mais altos.
    """
    require_minimum_role(db, acting_user_id, "supervisor")

    entry = get_order_stage_entry_by_id(db, entry_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo foi informado para atualização.",
        )

    apply_patch(entry, update_data)

    db.commit()
    db.refresh(entry)

    recalculate_order_completed_quantity(db, entry.order_id)

    return entry


def delete_order_stage_entry(
    db: Session,
    entry_id: int,
    acting_user_id: int,
) -> None:
    """
    Remove um lançamento de produção.
    Operação restrita a perfis mais altos.
    """
    require_minimum_role(db, acting_user_id, "supervisor")

    entry = get_order_stage_entry_by_id(db, entry_id)
    order_id = entry.order_id

    db.delete(entry)
    db.commit()

    recalculate_order_completed_quantity(db, order_id)


def get_order_stage_progress(
    db: Session,
    order_id: int,
) -> OrderProductionProgressResponse:
    """
    Retorna o progresso consolidado do pedido por etapa,
    calculado diretamente a partir de order_stage_entries.
    """
    order = _get_order_or_404(db, order_id)

    product_stages = (
        db.query(ProductStage)
        .options(joinedload(ProductStage.stage))
        .filter(ProductStage.product_id == order.product_id)
        .order_by(ProductStage.sequence.asc())
        .all()
    )

    totals_subquery = (
        db.query(
            OrderStageEntry.product_stage_id.label("product_stage_id"),
            func.sum(OrderStageEntry.quantity).label("quantity_completed"),
        )
        .filter(OrderStageEntry.order_id == order_id)
        .group_by(OrderStageEntry.product_stage_id)
        .subquery()
    )

    totals_map = {
        row.product_stage_id: int(row.quantity_completed or 0)
        for row in db.query(
            totals_subquery.c.product_stage_id,
            totals_subquery.c.quantity_completed,
        ).all()
    }

    stage_quantities = [totals_map.get(ps.id, 0) for ps in product_stages]

    stages = [
        OrderStageSummary(
            product_stage_id=ps.id,
            stage_id=ps.stage_id,
            stage_name=ps.stage.name,
            sequence=ps.sequence,
            quantity_completed=totals_map.get(ps.id, 0),
            completed_percent=_calculate_completed_percent(
                totals_map.get(ps.id, 0),
                order.quantity,
            ),
        )
        for ps in product_stages
    ]

    return OrderProductionProgressResponse(
        order_id=order.id,
        order_name=order.name,
        order_quantity=order.quantity,
        completed_quantity=order.completed_quantity,
        completed_percent=_calculate_completed_percent(
            order.completed_quantity,
            order.quantity,
        ),
        overall_progress_percent=_calculate_overall_progress_percent(
            stage_quantities=stage_quantities,
            order_quantity=order.quantity,
            total_stages=len(product_stages),
        ),
        is_ready_to_close=order.completed_quantity >= order.quantity,
        stages=stages,
    )