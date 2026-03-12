from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: str


class RoleRead(BaseModel):
    id: int
    name: str
    description: str

    model_config = {"from_attributes": True}