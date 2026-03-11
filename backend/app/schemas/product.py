from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    hcp_code: str
    version: str | None = None
    description: str | None = None

class ProductRead(BaseModel):
    id: int
    name: str
    hcp_code: str
    version: str | None
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}