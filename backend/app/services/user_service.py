from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.utils.permissions import (
    get_user_with_role,
    require_minimum_role,
    require_assignable_role,
)
from app.utils.patch import apply_patch
from app.utils.cpf import validate_cpf_digits


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_users(db: Session, is_active: bool | None = None):
    stmt = select(User).order_by(User.id)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    return db.execute(stmt).scalars().all()


def get_user_by_id(db: Session, user_id: int):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    return user


def get_assignable_roles(db: Session, acting_user_id: int):
    """
    Retorna as roles que o usuário logado pode atribuir a outro usuário.
    """
    acting_user = get_user_with_role(db, acting_user_id)

    stmt = select(Role).order_by(Role.level)

    # Master pode atribuir qualquer role
    if acting_user.role.code == "master":
        return db.execute(stmt).scalars().all()

    # Regra geral: só pode atribuir roles inferiores à própria
    stmt = stmt.where(Role.level < acting_user.role.level)

    return db.execute(stmt).scalars().all()


def create_user(db: Session, user_data: UserCreate, acting_user_id: int):
    # Apenas supervisor+ pode criar usuários
    require_minimum_role(db, acting_user_id, "supervisor")

    existing_user = db.execute(
        select(User).where(User.username == user_data.username)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nome de usuário já existe."
        )

    normalized_cpf = validate_cpf_digits(user_data.cpf)

    existing_cpf = db.execute(
        select(User).where(User.cpf == normalized_cpf)
    ).scalar_one_or_none()

    if existing_cpf:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já existe."
        )

    # Valida se o usuário logado pode atribuir a role solicitada
    require_assignable_role(db, acting_user_id, user_data.role_id)

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        cpf=normalized_cpf,
        role_id=user_data.role_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(db: Session, user_id: int, user_data: UserUpdate, acting_user_id: int):
    target_user = db.get(User, user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    acting_user = get_user_with_role(db, acting_user_id)
    target_user_with_role = get_user_with_role(db, user_id)

    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização."
        )

    # Normaliza/valida CPF se enviado
    if "cpf" in update_data:
        update_data["cpf"] = validate_cpf_digits(update_data["cpf"])


    # ---------------------------
    # Caso 1: master pode alterar tudo
    # ---------------------------
    if acting_user.role.code == "master":
        if "username" in update_data:
            existing_user = db.execute(
                select(User).where(
                    User.username == update_data["username"],
                    User.id != target_user.id,
                )
            ).scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Nome de usuário já existe."
                )

        if "cpf" in update_data:
            existing_cpf = db.execute(
                select(User).where(
                    User.cpf == update_data["cpf"],
                    User.id != target_user.id,
                )
            ).scalar_one_or_none()

            if existing_cpf:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="CPF já existe."
                )

        if "role_id" in update_data:
            require_assignable_role(db, acting_user_id, update_data["role_id"])

        if "new_password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("new_password"))

        # current_password não faz sentido quando outro usuário está alterando a conta
        update_data.pop("current_password", None)

        apply_patch(target_user, update_data)
        db.commit()
        db.refresh(target_user)
        return target_user


    # ---------------------------
    # Caso 2: usuário alterando a si mesmo
    # Permitido: apenas troca segura de senha
    # ---------------------------
    if acting_user.id == target_user.id:
        allowed_fields = {"current_password", "new_password"}

        invalid_fields = set(update_data.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode alterar sua própria senha."
            )

        if "current_password" not in update_data or "new_password" not in update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para alterar sua senha, informe current_password e new_password."
            )

        if not verify_password(update_data["current_password"], target_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta."
            )

        target_user.password_hash = hash_password(update_data["new_password"])
        db.commit()
        db.refresh(target_user)
        return target_user
    

    # ---------------------------
    # Caso 3: supervisor+ pode alterar apenas usuários operator
    # Permitido: username, display_name, cpf e new_password
    # ---------------------------
    require_minimum_role(db, acting_user_id, "supervisor")

    if target_user_with_role.role.code != "operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor+ só pode alterar usuários operator."
        )

    # current_password não é necessário quando um supervisor altera outro usuário
    update_data.pop("current_password", None)

    allowed_fields = {"username", "display_name", "cpf", "new_password"}
    invalid_fields = set(update_data.keys()) - allowed_fields

    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor+ só pode alterar username, display_name, cpf e senha de operators."
        )

    if not any(field in update_data for field in allowed_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos um campo permitido para atualização."
        )

    if "username" in update_data:
        existing_user = db.execute(
            select(User).where(
                User.username == update_data["username"],
                User.id != target_user.id,
            )
        ).scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nome de usuário já existe."
            )

        target_user.username = update_data["username"]

    if "display_name" in update_data:
        target_user.display_name = update_data["display_name"]

    if "cpf" in update_data:
        existing_cpf = db.execute(
            select(User).where(
                User.cpf == update_data["cpf"],
                User.id != target_user.id,
            )
        ).scalar_one_or_none()

        if existing_cpf:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CPF já existe."
            )

        target_user.cpf = update_data["cpf"]

    if "new_password" in update_data:
        target_user.password_hash = hash_password(update_data["new_password"])

    db.commit()
    db.refresh(target_user)
    return target_user


def delete_user(db: Session, user_id: int, acting_user_id: int):
    target_user = db.get(User, user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já está inativo."
        )

    acting_user = get_user_with_role(db, acting_user_id)
    target_user_with_role = get_user_with_role(db, user_id)

    # Master pode desativar qualquer usuário
    if acting_user.role.code == "master":
        target_user.is_active = False
        db.commit()
        db.refresh(target_user)
        return target_user

    # Supervisor+ pode desativar apenas operators
    require_minimum_role(db, acting_user_id, "supervisor")

    if target_user_with_role.role.code != "operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor+ só pode excluir usuários operator."
        )

    target_user.is_active = False
    db.commit()
    db.refresh(target_user)
    return target_user