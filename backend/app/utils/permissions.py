from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.role import Role


ROLE_HIERARCHY = {
    "operator": 10,
    "supervisor": 20,
    "manager": 30,
    "chief": 40,
    "it": 50,
    "admin": 60,
    "master": 70,
}


def get_user_with_role(db: Session, user_id: int):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if not user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário sem role associada."
        )

    return user


def get_role_level(role_name: str) -> int:
    level = ROLE_HIERARCHY.get(role_name)

    if level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role inválida para hierarquia: {role_name}."
        )

    return level


def require_minimum_role(db: Session, acting_user_id: int, minimum_role_name: str):
    acting_user = get_user_with_role(db, acting_user_id)

    acting_level = get_role_level(acting_user.role.name)
    minimum_level = get_role_level(minimum_role_name)

    if acting_level < minimum_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permissão insuficiente. É necessário ser {minimum_role_name}+."
        )

    return acting_user


def require_master_user(db: Session, acting_user_id: int):
    acting_user = get_user_with_role(db, acting_user_id)

    if acting_user.role.name != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários master podem realizar esta operação."
        )

    return acting_user


def get_role_by_id(db: Session, role_id: int):
    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada."
        )

    return role


def require_assignable_role(db: Session, acting_user_id: int, target_role_id: int):
    """
    Valida se o usuário logado pode atribuir a role informada.

    Regra:
    - o usuário só pode atribuir roles inferiores à sua própria
    - apenas master pode atribuir role master
    """

    acting_user = get_user_with_role(db, acting_user_id)
    target_role = get_role_by_id(db, target_role_id)

    acting_level = get_role_level(acting_user.role.name)
    target_level = get_role_level(target_role.name)

    # Role master só pode ser atribuída por master
    if target_role.name == "master" and acting_user.role.name != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários master podem atribuir a role master."
        )

    # Regra geral: a role atribuída deve ser inferior à do usuário logado
    if target_level >= acting_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode atribuir roles inferiores à sua."
        )

    return target_role