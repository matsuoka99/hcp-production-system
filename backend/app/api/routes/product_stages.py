from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product_stage import (
    ProductStageCreate,
    ProductStageItemRead,
    ProductStageItemWrite,
    ProductStageRead,
)
from app.services.product_stage_service import (
    create_product_stage,
    get_product_stages_by_product_id,
    list_product_stages,
    replace_product_stages,
)

router = APIRouter(tags=["product-stages"])


@router.post("/product-stages", response_model=ProductStageRead)
def create_product_stage_endpoint(
    data: ProductStageCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_product_stage(db, data, acting_user_id)


@router.get("/product-stages", response_model=list[ProductStageRead])
def list_product_stages_endpoint(db: Session = Depends(get_db)):
    return list_product_stages(db)


@router.get("/products/{product_id}/stages", response_model=list[ProductStageItemRead])
def get_product_stages_by_product_id_endpoint(
    product_id: int,
    db: Session = Depends(get_db),
):
    product_stages = get_product_stages_by_product_id(db, product_id)

    return [
        ProductStageItemRead(
            id=item.id,
            product_id=item.product_id,
            stage_id=item.stage_id,
            stage_name=item.stage.name,
            sequence=item.sequence,
        )
        for item in product_stages
    ]


@router.put("/products/{product_id}/stages", response_model=list[ProductStageItemRead])
def replace_product_stages_endpoint(
    product_id: int,
    items: list[ProductStageItemWrite],
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    product_stages = replace_product_stages(db, product_id, items, acting_user_id)

    return [
        ProductStageItemRead(
            id=item.id,
            product_id=item.product_id,
            stage_id=item.stage_id,
            stage_name=item.stage.name,
            sequence=item.sequence,
        )
        for item in product_stages
    ]