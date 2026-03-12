from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.kit import Kit
from app.models.client import Client
from app.models.product import Product
from app.models.user import User
from app.schemas.kit import KitCreate


def create_kit(db: Session, kit_data: KitCreate) -> Kit:
    product = db.get(Product, kit_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    user = db.get(User, kit_data.created_by_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário criador não encontrado.")

    kit = Kit(
        name=kit_data.name,
        product_id=kit_data.product_id,
        quantity=kit_data.quantity,
        remaining_quantity=kit_data.quantity,
        created_by_user_id=kit_data.created_by_user_id,
        description=kit_data.description,
        is_complete=kit_data.is_complete,
        is_active=True,
    )

    db.add(kit)
    db.commit()
    db.refresh(kit)

    return kit


def list_kits(db: Session) -> list[Kit]:
    kits = db.execute(select(Kit).order_by(Kit.id)).scalars().all()
    return kits