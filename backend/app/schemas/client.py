from pydantic import BaseModel

class ClientCreate(BaseModel):
    name: str
    cnpj: str

class ClientRead(BaseModel):
    id: int
    name: str
    cnpj: str
    is_active: bool

    model_config = {"from_attributes": True}