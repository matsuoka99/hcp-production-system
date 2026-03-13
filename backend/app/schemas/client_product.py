from pydantic import BaseModel


class ClientProductCreate(BaseModel):
    client_id: int
    product_id: int


class ClientProductRead(BaseModel):
    id: int
    client_id: int
    product_id: int

    model_config = {"from_attributes": True}


class ClientProductItemWrite(BaseModel):
    product_id: int


class ClientProductItemRead(BaseModel):
    id: int
    client_id: int
    product_id: int
    product_name: str
    hcp_code: str
    version: str | None
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}