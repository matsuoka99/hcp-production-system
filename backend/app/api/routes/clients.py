from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientRead
from app.services.client_service import create_client, list_clients

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead)
def create_client_endpoint(client_data: ClientCreate, db: Session = Depends(get_db)):
    return create_client(db, client_data)


@router.get("", response_model=list[ClientRead])
def list_clients_endpoint(db: Session = Depends(get_db)):
    return list_clients(db)