from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.stage import Stage
from app.schemas.stage import StageCreate, StageUpdate
from app.utils.permissions import require_minimum_role
from app.utils.patch import apply_patch


def get_stages(db: Session, is_active: bool | None = None):
    stmt = select(Stage).order_by(Stage.id)

    if is_active is not None:
        stmt = stmt.where(Stage.is_active == is_active)

    return db.execute(stmt).scalars().all()


def create_stage(db: Session, stage_data: StageCreate, acting_user_id: int):
    # Apenas supervisor+ pode criar etapas
    require_minimum_role(db, acting_user_id, "supervisor")

    existing_stage = db.execute(
        select(Stage).where(Stage.name == stage_data.name)
    ).scalar_one_or_none()

    if existing_stage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Etapa já existe."
        )

    stage = Stage(
        name=stage_data.name,
        is_active=True,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage


def update_stage(db: Session, stage_id: int, stage_data: StageUpdate, acting_user_id: int):
    # Apenas supervisor+ pode editar etapas
    require_minimum_role(db, acting_user_id, "supervisor")

    stage = db.get(Stage, stage_id)

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada."
        )

    update_data = stage_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização."
        )

    if "name" in update_data:
        existing_stage = db.execute(
            select(Stage).where(
                Stage.name == update_data["name"],
                Stage.id != stage.id,
            )
        ).scalar_one_or_none()

        if existing_stage:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Etapa já existe."
            )

    apply_patch(stage, update_data)

    db.commit()
    db.refresh(stage)

    return stage


def delete_stage(db: Session, stage_id: int, acting_user_id: int):
    # Apenas supervisor+ pode desativar etapas
    require_minimum_role(db, acting_user_id, "supervisor")

    stage = db.get(Stage, stage_id)

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada."
        )

    if not stage.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Etapa já está inativa."
        )

    stage.is_active = False

    db.commit()
    db.refresh(stage)

    return stage

def get_stage_by_id(db: Session, stage_id: int):
    stage = db.get(Stage, stage_id)

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada."
        )

    return stage