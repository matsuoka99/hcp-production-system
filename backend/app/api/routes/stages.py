from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stage import StageCreate, StageRead
from app.services.stage_service import create_stage, list_stages

router = APIRouter(prefix="/stages", tags=["stages"])


@router.post("", response_model=StageRead)
def create_stage_endpoint(stage_data: StageCreate, db: Session = Depends(get_db)):
    return create_stage(db, stage_data)


@router.get("", response_model=list[StageRead])
def list_stages_endpoint(db: Session = Depends(get_db)):
    return list_stages(db)