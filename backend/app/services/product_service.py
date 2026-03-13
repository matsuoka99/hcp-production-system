from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.permissions import require_minimum_role
from app.utils.patch import apply_patch


def get_products(
    db: Session,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = select(Product)

    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    if search:
        stmt = stmt.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.hcp_code.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    stmt = stmt.order_by(Product.id).limit(limit).offset(offset)

    return db.execute(stmt).scalars().all()


def get_product_by_id(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    return product


def create_product(db: Session, product_data: ProductCreate, acting_user_id: int):
    # Apenas supervisor+ pode criar produtos
    require_minimum_role(db, acting_user_id, "supervisor")

    existing_product_by_name = db.execute(
        select(Product).where(Product.name == product_data.name)
    ).scalar_one_or_none()

    if existing_product_by_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Produto com este nome já existe.",
        )

    existing_product_by_hcp_code = db.execute(
        select(Product).where(Product.hcp_code == product_data.hcp_code)
    ).scalar_one_or_none()

    if existing_product_by_hcp_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Produto com este HCP code já existe.",
        )

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


def update_product(
    db: Session,
    product_id: int,
    product_data: ProductUpdate,
    acting_user_id: int,
):
    # Apenas supervisor+ pode editar produtos
    require_minimum_role(db, acting_user_id, "supervisor")

    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    update_data = product_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização.",
        )

    if "name" in update_data:
        existing_product_by_name = db.execute(
            select(Product).where(
                Product.name == update_data["name"],
                Product.id != product.id,
            )
        ).scalar_one_or_none()

        if existing_product_by_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto com este nome já existe.",
            )

    if "hcp_code" in update_data:
        existing_product_by_hcp_code = db.execute(
            select(Product).where(
                Product.hcp_code == update_data["hcp_code"],
                Product.id != product.id,
            )
        ).scalar_one_or_none()

        if existing_product_by_hcp_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto com este HCP code já existe.",
            )

    apply_patch(product, update_data)

    db.commit()
    db.refresh(product)

    return product


def delete_product(db: Session, product_id: int, acting_user_id: int):
    # Apenas supervisor+ pode desativar produtos
    require_minimum_role(db, acting_user_id, "supervisor")

    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produto já está inativo.",
        )

    product.is_active = False

    db.commit()
    db.refresh(product)

    return product