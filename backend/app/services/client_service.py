from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.client import Client
from app.schemas.client import ClientCreate


def create_client(db: Session, client_data: ClientCreate) -> Client:
    existing_client = db.execute(
        select(Client).where(Client.cnpj == client_data.cnpj)
    ).scalar_one_or_none()

    if existing_client:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    client = Client(
        name=client_data.name,
        cnpj=client_data.cnpj,
        is_active=True,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


def list_clients(db: Session) -> list[Client]:
    clients = db.execute(select(Client).order_by(Client.id)).scalars().all()
    return clients