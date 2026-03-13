from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client_product import (
    ClientProductCreate,
    ClientProductItemRead,
    ClientProductItemWrite,
    ClientProductRead,
)
from app.services.client_product_service import (
    create_client_product,
    get_client_products_by_client_id,
    list_client_products,
    replace_client_products,
)

router = APIRouter(tags=["client-products"])



@router.post("/client-products", response_model=ClientProductRead)
def create_client_product_endpoint(
    data: ClientProductCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_client_product(db, data, acting_user_id)


@router.get("/client-products", response_model=list[ClientProductRead])
def list_client_products_endpoint(db: Session = Depends(get_db)):
    return list_client_products(db)


@router.get("/clients/{client_id}/products", response_model=list[ClientProductItemRead])
def get_client_products_by_client_id_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
):
    client_products = get_client_products_by_client_id(db, client_id)

    return [
        ClientProductItemRead(
            id=item.id,
            client_id=item.client_id,
            product_id=item.product_id,
            product_name=item.product.name,
            hcp_code=item.product.hcp_code,
            version=item.product.version,
            description=item.product.description,
            is_active=item.product.is_active,
        )
        for item in client_products
    ]


@router.put("/clients/{client_id}/products", response_model=list[ClientProductItemRead])
def replace_client_products_endpoint(
    client_id: int,
    items: list[ClientProductItemWrite],
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    client_products = replace_client_products(db, client_id, items, acting_user_id)

    return [
        ClientProductItemRead(
            id=item.id,
            client_id=item.client_id,
            product_id=item.product_id,
            product_name=item.product.name,
            hcp_code=item.product.hcp_code,
            version=item.product.version,
            description=item.product.description,
            is_active=item.product.is_active,
        )
        for item in client_products
    ]