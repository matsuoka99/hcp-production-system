from pydantic import BaseModel, Field
from datetime import datetime


class OrderKitCreate(BaseModel):
    order_id: int
    kit_id: int
    allocated_quantity: int = Field(gt=0)
    allocated_by_user_id: int


class OrderKitRead(BaseModel):
    id: int
    order_id: int
    kit_id: int
    allocated_quantity: int
    allocated_at: datetime
    allocated_by_user_id: int

    model_config = {"from_attributes": True}


class AvailableKitRead(BaseModel):
    kit_id: int
    name: str
    remaining_quantity: int


class OrderAvailableKitsRead(BaseModel):
    order_id: int
    order_quantity: int
    already_allocated: int
    remaining_to_allocate: int
    can_fulfill_fully: bool
    available_kits: list[AvailableKitRead]