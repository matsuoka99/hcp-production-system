from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate
from app.utils.permissions import require_master_user
from app.utils.patch import apply_patch


def create_role(db: Session, role_data: RoleCreate, acting_user_id: int) -> Role:
    require_master_user(db, acting_user_id)

    existing_role = db.execute(
        select(Role).where(Role.name == role_data.name)
    ).scalar_one_or_none()

    if existing_role:
        raise HTTPException(status_code=400, detail="Role já cadastrada.")

    role = Role(
        name=role_data.name,
        description=role_data.description,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def list_roles(db: Session) -> list[Role]:
    roles = db.execute(select(Role).order_by(Role.id)).scalars().all()
    return roles


def get_role_by_id(db: Session, role_id: int) -> Role:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrada.")

    return role


def update_role(
    db: Session,
    role_id: int,
    role_data: RoleUpdate,
    acting_user_id: int,
) -> Role:
    require_master_user(db, acting_user_id)

    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrada.")

    update_data = role_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_role = db.execute(
            select(Role).where(
                Role.name == update_data["name"],
                Role.id != role_id,
            )
        ).scalar_one_or_none()

        if existing_role:
            raise HTTPException(
                status_code=400,
                detail="Já existe outra role com esse nome.",
            )

    apply_patch(role, update_data)

    db.commit()
    db.refresh(role)

    return role