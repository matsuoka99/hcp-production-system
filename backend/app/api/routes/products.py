from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import create_product, list_products

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductRead)
def create_product_endpoint(product_data: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product_data)


@router.get("", response_model=list[ProductRead])
def list_products_endpoint(db: Session = Depends(get_db)):
    return list_products(db)