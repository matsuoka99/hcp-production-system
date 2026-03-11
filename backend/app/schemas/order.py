from pydantic import BaseModel, Field
from datetime import date

class OrderCreate(BaseModel):
    name: str
    client_id: int
    product_id: int
    quantity: int = Field(gt=0)
    created_by_user_id: int
    description: str | None = None
    delivery_date: date

class OrderRead(BaseModel):
    id: int
    name: str
    client_id: int
    product_id: int
    quantity: int
    completed_quantity: int
    created_by_user_id: int
    description: str | None
    delivery_date: date
    is_active: bool

    model_config = {"from_attributes": True}