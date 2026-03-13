from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User


def get_user_with_role(db: Session, user_id: int) -> User:
    """
    Busca um usuário e garante que ele exista e possua role associada.
    """
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo."
        )

    if not user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem role associada."
        )

    return user


def get_role_by_id(db: Session, role_id: int) -> Role:
    """
    Busca uma role pelo id.
    """
    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada."
        )

    return role


def get_role_by_code(db: Session, role_code: str) -> Role:
    """
    Busca uma role pelo code.
    """
    role = db.execute(
        select(Role).where(Role.code == role_code)
    ).scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada."
        )

    return role


def require_minimum_role(
    db: Session,
    acting_user_id: int,
    minimum_role_code: str,
) -> User:
    """
    Garante que o usuário possua no mínimo a role informada.

    A comparação é feita pelo level da role.
    Exemplo:
    - require_minimum_role(..., "supervisor")
    """
    acting_user = get_user_with_role(db, acting_user_id)
    minimum_role = get_role_by_code(db, minimum_role_code)

    if acting_user.role.level < minimum_role.level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permissão insuficiente. É necessário ser {minimum_role.code}+."
        )

    return acting_user


def require_master_user(db: Session, acting_user_id: int) -> User:
    """
    Garante que o usuário seja master.
    """
    acting_user = get_user_with_role(db, acting_user_id)

    if acting_user.role.code != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários master podem realizar esta operação."
        )

    return acting_user


def require_assignable_role(db: Session, acting_user_id: int, target_role_id: int) -> Role:
    """
    Valida se o usuário logado pode atribuir a role informada.

    Regras:
    - o usuário só pode atribuir roles inferiores à sua própria
    - apenas master pode atribuir a role master
    """
    acting_user = get_user_with_role(db, acting_user_id)
    target_role = get_role_by_id(db, target_role_id)

    # Apenas master pode atribuir a role master
    if target_role.code == "master":
        if acting_user.role.code != "master":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas usuários master podem atribuir a role master."
            )
        return target_role

    # Regra geral: só pode atribuir roles inferiores à própria
    if target_role.level >= acting_user.role.level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode atribuir roles inferiores à sua."
        )

    return target_role