from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate


def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = db.execute(
        select(User).where(User.username == user_data.username)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado.")

    role = db.get(Role, user_data.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrada.")

    user = User(
        username=user_data.username,
        password_hash=user_data.password_hash,
        role_id=user_data.role_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def list_users(db: Session) -> list[User]:
    users = db.execute(select(User).order_by(User.id)).scalars().all()
    return users