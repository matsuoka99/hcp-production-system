from pydantic import BaseModel
from datetime import date


class OrderCreate(BaseModel):
    name: str
    client_id: int
    product_id: int
    quantity: int
    delivery_date: date
    description: str | None = None


class OrderUpdate(BaseModel):
    description: str | None = None
    delivery_date: date | None = None


class OrderRead(BaseModel):
    id: int
    name: str
    client_id: int
    product_id: int
    quantity: int
    completed_quantity: int
    delivery_date: date
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}