from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.stage import Stage
from app.schemas.stage import StageCreate


def create_stage(db: Session, stage_data: StageCreate) -> Stage:
    existing_stage = db.execute(
        select(Stage).where(Stage.name == stage_data.name)
    ).scalar_one_or_none()

    if existing_stage:
        raise HTTPException(status_code=400, detail="Etapa já cadastrada.")

    stage = Stage(
        name=stage_data.name,
        is_active=True,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage


def list_stages(db: Session) -> list[Stage]:
    stages = db.execute(select(Stage).order_by(Stage.id)).scalars().all()
    return stages