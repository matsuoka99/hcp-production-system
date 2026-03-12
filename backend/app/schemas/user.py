from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password_hash: str
    role_id: int


class UserRead(BaseModel):
    id: int
    username: str
    role_id: int
    is_active: bool

    model_config = {"from_attributes": True}