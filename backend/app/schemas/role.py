from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    level: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=255)


class RoleUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    level: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=255)


class RoleRead(BaseModel):
    id: int
    code: str
    name: str
    level: int
    description: str

    model_config = {"from_attributes": True}