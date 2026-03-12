from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role_id: int


class UserRead(BaseModel):
    id: int
    username: str
    role_id: int
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    current_password: str | None = Field(default=None, min_length=6, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)
    role_id: int | None = None
    is_active: bool | None = None