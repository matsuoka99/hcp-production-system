from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services.client_service import (
    create_client,
    delete_client,
    get_client_by_id,
    get_clients,
    update_client,
)


router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def get_clients_route(
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return get_clients(
        db,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )

@router.post("", response_model=ClientRead)
def create_client_route(
    client_data: ClientCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return create_client(db, client_data, acting_user_id)


@router.get("/{client_id}", response_model=ClientRead)
def get_client_by_id_route(
    client_id: int,
    db: Session = Depends(get_db),
):
    return get_client_by_id(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def update_client_route(
    client_id: int,
    client_data: ClientUpdate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return update_client(db, client_id, client_data, acting_user_id)


@router.delete("/{client_id}", response_model=ClientRead)
def delete_client_route(
    client_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return delete_client(db, client_id, acting_user_id)