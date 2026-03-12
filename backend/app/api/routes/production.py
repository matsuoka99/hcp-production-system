from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.production import ProductionEntryCreate, ProductionEntryRead
from app.services.production_service import (
    create_production_entry,
    list_production_entries,
)

router = APIRouter(prefix="/production-entries", tags=["production"])


@router.post("", response_model=ProductionEntryRead)
def create_production_entry_endpoint(
    entry_data: ProductionEntryCreate,
    db: Session = Depends(get_db)
):
    return create_production_entry(db, entry_data)


@router.get("", response_model=list[ProductionEntryRead])
def list_production_entries_endpoint(db: Session = Depends(get_db)):
    return list_production_entries(db)