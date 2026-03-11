from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.stage import Stage
from app.schemas.stage import StageCreate, StageRead

router = APIRouter(prefix="/stages", tags=["stages"])

@router.post("", response_model=StageRead)
def create_stage(stage_data: StageCreate, db: Session = Depends(get_db)):
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

@router.get("", response_model=list[StageRead])
def list_stages(db: Session = Depends(get_db)):
    stages = db.execute(select(Stage).order_by(Stage.id)).scalars().all()
    return stages