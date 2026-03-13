from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate
from app.utils.patch import apply_patch
from app.utils.permissions import require_master_user


def create_role(db: Session, role_data: RoleCreate, acting_user_id: int) -> Role:
    """
    Cria uma nova role.
    Apenas usuários master podem realizar esta operação.
    """
    require_master_user(db, acting_user_id)

    existing_role_by_code = db.execute(
        select(Role).where(Role.code == role_data.code)
    ).scalar_one_or_none()

    if existing_role_by_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma role com esse código."
        )

    existing_role_by_name = db.execute(
        select(Role).where(Role.name == role_data.name)
    ).scalar_one_or_none()

    if existing_role_by_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma role com esse nome."
        )

    existing_role_by_level = db.execute(
        select(Role).where(Role.level == role_data.level)
    ).scalar_one_or_none()

    if existing_role_by_level:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma role com esse nível."
        )

    role = Role(
        code=role_data.code,
        name=role_data.name,
        level=role_data.level,
        description=role_data.description,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def get_roles(db: Session) -> list[Role]:
    """
    Retorna a lista de roles ordenada por nível hierárquico.
    """
    return db.execute(
        select(Role).order_by(Role.level)
    ).scalars().all()


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


def update_role(
    db: Session,
    role_id: int,
    role_data: RoleUpdate,
    acting_user_id: int,
) -> Role:
    """
    Atualiza uma role existente.
    Apenas usuários master podem realizar esta operação.
    """
    require_master_user(db, acting_user_id)

    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada."
        )

    update_data = role_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização."
        )

    if "code" in update_data:
        existing_role_by_code = db.execute(
            select(Role).where(
                Role.code == update_data["code"],
                Role.id != role_id,
            )
        ).scalar_one_or_none()

        if existing_role_by_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe outra role com esse código."
            )

    if "name" in update_data:
        existing_role_by_name = db.execute(
            select(Role).where(
                Role.name == update_data["name"],
                Role.id != role_id,
            )
        ).scalar_one_or_none()

        if existing_role_by_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe outra role com esse nome."
            )

    if "level" in update_data:
        existing_role_by_level = db.execute(
            select(Role).where(
                Role.level == update_data["level"],
                Role.id != role_id,
            )
        ).scalar_one_or_none()

        if existing_role_by_level:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe outra role com esse nível."
            )

    apply_patch(role, update_data)

    db.commit()
    db.refresh(role)

    return role