from pydantic import BaseModel

class StageCreate(BaseModel):
    name: str

class StageRead(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}