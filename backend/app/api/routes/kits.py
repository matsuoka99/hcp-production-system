from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.kit import KitCreate, KitRead
from app.services.kit_service import create_kit, list_kits

router = APIRouter(prefix="/kits", tags=["kits"])


@router.post("", response_model=KitRead)
def create_kit_endpoint(kit_data: KitCreate, db: Session = Depends(get_db)):
    return create_kit(db, kit_data)


@router.get("", response_model=list[KitRead])
def list_kits_endpoint(db: Session = Depends(get_db)):
    return list_kits(db)