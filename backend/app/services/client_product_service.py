from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.client import Client
from app.models.client_product import ClientProduct
from app.models.product import Product
from app.schemas.client_product import ClientProductCreate, ClientProductItemWrite
from app.utils.permissions import require_minimum_role


def create_client_product(
    db: Session,
    data: ClientProductCreate,
    acting_user_id: int,
) -> ClientProduct:
    # Apenas supervisor+ pode vincular produtos a clientes
    require_minimum_role(db, acting_user_id, "supervisor")

    client = db.get(Client, data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    existing_link = db.execute(
        select(ClientProduct).where(
            ClientProduct.client_id == data.client_id,
            ClientProduct.product_id == data.product_id,
        )
    ).scalar_one_or_none()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esse produto já está vinculado a esse cliente.",
        )

    link = ClientProduct(
        client_id=data.client_id,
        product_id=data.product_id,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link


def list_client_products(db: Session) -> list[ClientProduct]:
    return db.execute(
        select(ClientProduct).order_by(ClientProduct.client_id, ClientProduct.product_id)
    ).scalars().all()


def get_client_products_by_client_id(
    db: Session,
    client_id: int,
) -> list[ClientProduct]:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    return db.execute(
        select(ClientProduct)
        .options(joinedload(ClientProduct.product))
        .where(ClientProduct.client_id == client_id)
        .order_by(ClientProduct.id)
    ).scalars().all()


def replace_client_products(
    db: Session,
    client_id: int,
    items: list[ClientProductItemWrite],
    acting_user_id: int,
) -> list[ClientProduct]:
    # Apenas supervisor+ pode editar os produtos vinculados ao cliente
    require_minimum_role(db, acting_user_id, "supervisor")

    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    product_ids = [item.product_id for item in items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido repetir produtos no mesmo cliente.",
        )

    if product_ids:
        existing_products = db.execute(
            select(Product).where(Product.id.in_(product_ids))
        ).scalars().all()

        existing_product_ids = {product.id for product in existing_products}
        missing_product_ids = [
            product_id for product_id in product_ids
            if product_id not in existing_product_ids
        ]

        if missing_product_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produtos não encontrados: {missing_product_ids}.",
            )

    current_links = db.execute(
        select(ClientProduct).where(ClientProduct.client_id == client_id)
    ).scalars().all()

    for link in current_links:
        db.delete(link)

    db.flush()

    new_links: list[ClientProduct] = []

    for item in items:
        link = ClientProduct(
            client_id=client_id,
            product_id=item.product_id,
        )
        db.add(link)
        new_links.append(link)

    db.commit()

    return db.execute(
        select(ClientProduct)
        .options(joinedload(ClientProduct.product))
        .where(ClientProduct.client_id == client_id)
        .order_by(ClientProduct.id)
    ).scalars().all()