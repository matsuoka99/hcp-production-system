from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: str


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    

class RoleRead(BaseModel):
    id: int
    name: str
    description: str

    model_config = {"from_attributes": True}