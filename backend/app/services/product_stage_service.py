from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.product_stage import ProductStage
from app.models.stage import Stage
from app.schemas.product_stage import (
    ProductStageCreate,
    ProductStageItemWrite,
)
from app.utils.permissions import require_minimum_role


def create_product_stage(
    db: Session,
    data: ProductStageCreate,
    acting_user_id: int,
) -> ProductStage:
    # Apenas supervisor+ pode vincular etapas a produtos
    require_minimum_role(db, acting_user_id, "supervisor")

    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    stage = db.get(Stage, data.stage_id)
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada.",
        )

    existing_same_stage = db.execute(
        select(ProductStage).where(
            ProductStage.product_id == data.product_id,
            ProductStage.stage_id == data.stage_id,
        )
    ).scalar_one_or_none()

    if existing_same_stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essa etapa já está vinculada a esse produto.",
        )

    existing_same_sequence = db.execute(
        select(ProductStage).where(
            ProductStage.product_id == data.product_id,
            ProductStage.sequence == data.sequence,
        )
    ).scalar_one_or_none()

    if existing_same_sequence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essa sequência já está em uso para esse produto.",
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


def list_product_stages(db: Session) -> list[ProductStage]:
    return db.execute(
        select(ProductStage).order_by(ProductStage.product_id, ProductStage.sequence)
    ).scalars().all()


def get_product_stages_by_product_id(db: Session, product_id: int) -> list[ProductStage]:
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    return db.execute(
        select(ProductStage)
        .options(joinedload(ProductStage.stage))
        .where(ProductStage.product_id == product_id)
        .order_by(ProductStage.sequence, ProductStage.id)
    ).scalars().all()


def replace_product_stages(
    db: Session,
    product_id: int,
    items: list[ProductStageItemWrite],
    acting_user_id: int,
) -> list[ProductStage]:
    # Apenas supervisor+ pode editar a sequência de etapas do produto
    require_minimum_role(db, acting_user_id, "supervisor")

    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    stage_ids = [item.stage_id for item in items]
    sequences = [item.sequence for item in items]

    if len(stage_ids) != len(set(stage_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido repetir etapas no mesmo produto.",
        )

    if len(sequences) != len(set(sequences)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido repetir sequências no mesmo produto.",
        )

    if items:
        existing_stages = db.execute(
            select(Stage).where(Stage.id.in_(stage_ids))
        ).scalars().all()

        existing_stage_ids = {stage.id for stage in existing_stages}
        missing_stage_ids = [stage_id for stage_id in stage_ids if stage_id not in existing_stage_ids]

        if missing_stage_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapas não encontradas: {missing_stage_ids}.",
            )

    # Remove todos os vínculos atuais do produto
    current_links = db.execute(
        select(ProductStage).where(ProductStage.product_id == product_id)
    ).scalars().all()

    for link in current_links:
        db.delete(link)

    db.flush()

    # Recria os vínculos conforme a configuração final enviada pelo frontend
    new_links: list[ProductStage] = []

    for item in items:
        link = ProductStage(
            product_id=product_id,
            stage_id=item.stage_id,
            sequence=item.sequence,
        )
        db.add(link)
        new_links.append(link)

    db.commit()

    return db.execute(
        select(ProductStage)
        .options(joinedload(ProductStage.stage))
        .where(ProductStage.product_id == product_id)
        .order_by(ProductStage.sequence, ProductStage.id)
    ).scalars().all()