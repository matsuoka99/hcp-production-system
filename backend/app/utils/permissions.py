from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User


ROLE_HIERARCHY = {
    "operator": 10,
    "supervisor": 20,
    "manager": 30,
    "chief": 40,
    "it": 50,
    "admin": 60,
    "master": 70,
}


def get_user_with_role(db: Session, acting_user_id: int) -> User:
    user = db.get(User, acting_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    if not user.role:
        raise HTTPException(status_code=403, detail="Usuário sem role associada.")

    return user


def get_role_level(role_name: str) -> int:
    return ROLE_HIERARCHY.get(role_name.lower(), 0)


def require_minimum_role(
    db: Session,
    acting_user_id: int,
    minimum_role: str,
) -> User:
    user = get_user_with_role(db, acting_user_id)

    user_role_level = get_role_level(user.role.name)
    minimum_role_level = get_role_level(minimum_role)

    if user_role_level < minimum_role_level:
        raise HTTPException(
            status_code=403,
            detail=f"Ação permitida apenas para usuários com role '{minimum_role}' ou superior."
        )

    return user


def require_master_user(db: Session, acting_user_id: int) -> User:
    return require_minimum_role(db, acting_user_id, "master")