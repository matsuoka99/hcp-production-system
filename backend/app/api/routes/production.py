from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.order_stage_entry import OrderStageEntry
from app.models.order import Order
from app.models.product_stage import ProductStage
from app.models.user import User
from app.schemas.production import ProductionEntryCreate, ProductionEntryRead

router = APIRouter(prefix="/production-entries", tags=["production"])

@router.post("", response_model=ProductionEntryRead)
def create_production_entry(entry_data: ProductionEntryCreate, db: Session = Depends(get_db)):
    order = db.get(Order, entry_data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    product_stage = db.get(ProductStage, entry_data.product_stage_id)
    if not product_stage:
        raise HTTPException(status_code=404, detail="Etapa do produto não encontrada.")

    user = db.get(User, entry_data.created_by_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if product_stage.product_id != order.product_id:
        raise HTTPException(
            status_code=400,
            detail="A etapa informada não pertence ao produto do pedido."
        )

    entry = OrderStageEntry(
        order_id=entry_data.order_id,
        product_stage_id=entry_data.product_stage_id,
        quantity=entry_data.quantity,
        created_by_user_id=entry_data.created_by_user_id,
        description=entry_data.description,
        performed_at=entry_data.performed_at,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry

@router.get("", response_model=list[ProductionEntryRead])
def list_production_entries(db: Session = Depends(get_db)):
    entries = db.execute(
        select(OrderStageEntry).order_by(OrderStageEntry.id)
    ).scalars().all()
    return entries