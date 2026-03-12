from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role import RoleCreate, RoleRead
from app.services.role_service import create_role, list_roles

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", response_model=RoleRead)
def create_role_endpoint(role_data: RoleCreate, db: Session = Depends(get_db)):
    return create_role(db, role_data)


@router.get("", response_model=list[RoleRead])
def list_roles_endpoint(db: Session = Depends(get_db)):
    return list_roles(db)