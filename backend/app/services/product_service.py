from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.schemas.product import ProductCreate


def create_product(db: Session, product_data: ProductCreate) -> Product:
    existing_product = db.execute(
        select(Product).where(Product.hcp_code == product_data.hcp_code)
    ).scalar_one_or_none()

    if existing_product:
        raise HTTPException(status_code=400, detail="HCP code já cadastrado.")

    product = Product(
        name=product_data.name,
        hcp_code=product_data.hcp_code,
        version=product_data.version,
        description=product_data.description,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def list_products(db: Session) -> list[Product]:
    products = db.execute(select(Product).order_by(Product.id)).scalars().all()
    return products