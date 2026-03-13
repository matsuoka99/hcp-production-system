from pydantic import BaseModel, Field


class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StageRead(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class StageUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None