from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    cnpj: str = Field(min_length=14, max_length=18)


class ClientRead(BaseModel):
    id: int
    name: str
    cnpj: str
    is_active: bool

    model_config = {"from_attributes": True}


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    cnpj: str | None = Field(default=None, min_length=14, max_length=18)
    is_active: bool | None = None