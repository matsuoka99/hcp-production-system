from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product_stage import ProductStageCreate, ProductStageRead
from app.services.product_stage_service import (
    create_product_stage,
    list_product_stages,
)

router = APIRouter(prefix="/product-stages", tags=["product-stages"])


@router.post("", response_model=ProductStageRead)
def create_product_stage_endpoint(
    data: ProductStageCreate,
    db: Session = Depends(get_db),
):
    return create_product_stage(db, data)


@router.get("", response_model=list[ProductStageRead])
def list_product_stages_endpoint(db: Session = Depends(get_db)):
    return list_product_stages(db)