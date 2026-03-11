from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("", response_model=ClientRead)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    existing_client = db.execute(
        select(Client).where(Client.cnpj == client_data.cnpj)
    ).scalar_one_or_none()

    if existing_client:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    client = Client(
        name=client_data.name,
        cnpj=client_data.cnpj,
        is_active=True
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client

@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    clients = db.execute(select(Client).order_by(Client.id)).scalars().all()
    return clients