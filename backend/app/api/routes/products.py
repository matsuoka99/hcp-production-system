from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import (
    create_product,
    delete_product,
    get_product_by_id,
    get_products,
    update_product,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def get_products_route(
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return get_products(
        db,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProductRead)
def create_product_route(
    product_data: ProductCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_product(db, product_data, acting_user_id)


@router.get("/{product_id}", response_model=ProductRead)
def get_product_by_id_route(
    product_id: int,
    db: Session = Depends(get_db),
):
    return get_product_by_id(db, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product_route(
    product_id: int,
    product_data: ProductUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_product(db, product_id, product_data, acting_user_id)


@router.delete("/{product_id}", response_model=ProductRead)
def delete_product_route(
    product_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return delete_product(db, product_id, acting_user_id)