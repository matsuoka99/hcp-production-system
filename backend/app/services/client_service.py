from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.utils.permissions import require_minimum_role
from app.utils.patch import apply_patch
from app.utils.cnpj import validate_cnpj_digits, normalize_cnpj


def get_clients(
    db: Session,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = select(Client)

    if is_active is not None:
        stmt = stmt.where(Client.is_active == is_active)

    if search:
        normalized_cnpj = normalize_cnpj(search)

        filters = [Client.name.ilike(f"%{search}%")]

        if normalized_cnpj:
            filters.append(Client.cnpj.ilike(f"%{normalized_cnpj}%"))

        stmt = stmt.where(or_(*filters))

    stmt = stmt.order_by(Client.id).limit(limit).offset(offset)

    return db.execute(stmt).scalars().all()

def get_client_by_id(db: Session, client_id: int):
    client = db.get(Client, client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    return client


def create_client(db: Session, client_data: ClientCreate, acting_user_id: int):
    # Apenas supervisor+ pode criar clientes
    require_minimum_role(db, acting_user_id, "supervisor")

    normalized_cnpj = validate_cnpj_digits(client_data.cnpj)

    existing_client_by_name = db.execute(
        select(Client).where(Client.name == client_data.name)
    ).scalar_one_or_none()

    if existing_client_by_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cliente com este nome já existe."
        )

    existing_client_by_cnpj = db.execute(
        select(Client).where(Client.cnpj == normalized_cnpj)
    ).scalar_one_or_none()

    if existing_client_by_cnpj:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cliente com este CNPJ já existe."
        )

    client = Client(
        name=client_data.name,
        cnpj=normalized_cnpj,
        is_active=True,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


def update_client(db: Session, client_id: int, client_data: ClientUpdate, acting_user_id: int):
    # Apenas supervisor+ pode editar clientes
    require_minimum_role(db, acting_user_id, "supervisor")

    client = db.get(Client, client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    update_data = client_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização."
        )

    if "name" in update_data:
        existing_client_by_name = db.execute(
            select(Client).where(
                Client.name == update_data["name"],
                Client.id != client.id,
            )
        ).scalar_one_or_none()

        if existing_client_by_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente com este nome já existe."
            )

    if "cnpj" in update_data:
        normalized_cnpj = validate_cnpj_digits(update_data["cnpj"])

        existing_client_by_cnpj = db.execute(
            select(Client).where(
                Client.cnpj == normalized_cnpj,
                Client.id != client.id,
            )
        ).scalar_one_or_none()

        if existing_client_by_cnpj:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente com este CNPJ já existe."
            )

        update_data["cnpj"] = normalized_cnpj

    apply_patch(client, update_data)

    db.commit()
    db.refresh(client)

    return client


def delete_client(db: Session, client_id: int, acting_user_id: int):
    # Apenas supervisor+ pode desativar clientes
    require_minimum_role(db, acting_user_id, "supervisor")

    client = db.get(Client, client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente já está inativo."
        )

    client.is_active = False

    db.commit()
    db.refresh(client)

    return client