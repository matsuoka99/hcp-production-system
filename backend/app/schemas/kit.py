from datetime import datetime
from pydantic import BaseModel


class KitCreate(BaseModel):
    name: str
    product_id: int
    quantity: int
    description: str | None = None
    is_complete: bool = False


class KitUpdate(BaseModel):
    description: str | None = None
    is_complete: bool | None = None
    is_active: bool | None = None


class KitRead(BaseModel):
    id: int
    name: str
    product_id: int
    quantity: int
    remaining_quantity: int
    description: str | None
    is_complete: bool
    created_at: datetime
    created_by_user_id: int
    closed_at: datetime | None
    closed_by_user_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}