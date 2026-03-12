from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.role import Role
from app.schemas.role import RoleCreate


def create_role(db: Session, role_data: RoleCreate) -> Role:
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