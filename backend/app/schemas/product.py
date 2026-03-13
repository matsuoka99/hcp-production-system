from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    hcp_code: str
    version: str | None = None
    description: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    hcp_code: str | None = None
    version: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    name: str
    hcp_code: str
    version: str | None
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}