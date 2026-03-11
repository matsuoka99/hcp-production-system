from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.product_stage import ProductStage
from app.models.product import Product
from app.models.stage import Stage
from app.schemas.product_stage import ProductStageCreate, ProductStageRead

router = APIRouter(prefix="/product-stages", tags=["product-stages"])

@router.post("", response_model=ProductStageRead)
def create_product_stage(data: ProductStageCreate, db: Session = Depends(get_db)):
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    stage = db.get(Stage, data.stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa não encontrada.")

    existing_same_stage = db.execute(
        select(ProductStage).where(
            ProductStage.product_id == data.product_id,
            ProductStage.stage_id == data.stage_id,
        )
    ).scalar_one_or_none()

    if existing_same_stage:
        raise HTTPException(
            status_code=400,
            detail="Essa etapa já está vinculada a esse produto."
        )

    existing_same_sequence = db.execute(
        select(ProductStage).where(
            ProductStage.product_id == data.product_id,
            ProductStage.sequence == data.sequence,
        )
    ).scalar_one_or_none()

    if existing_same_sequence:
        raise HTTPException(
            status_code=400,
            detail="Essa sequência já está em uso para esse produto."
        )

    product_stage = ProductStage(
        product_id=data.product_id,
        stage_id=data.stage_id,
        sequence=data.sequence,
    )

    db.add(product_stage)
    db.commit()
    db.refresh(product_stage)

    return product_stage

@router.get("", response_model=list[ProductStageRead])
def list_product_stages(db: Session = Depends(get_db)):
    product_stages = db.execute(
        select(ProductStage).order_by(ProductStage.product_id, ProductStage.sequence)
    ).scalars().all()

    return product_stages