from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user_endpoint(user_data: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_data)


@router.get("", response_model=list[UserRead])
def list_users_endpoint(db: Session = Depends(get_db)):
    return list_users(db)