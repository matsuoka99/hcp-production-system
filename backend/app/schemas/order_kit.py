from datetime import datetime
from pydantic import BaseModel


class OrderKitCreate(BaseModel):
    order_id: int
    kit_id: int


class OrderKitRead(BaseModel):
    id: int
    order_id: int
    kit_id: int
    allocated_quantity: int
    allocated_at: datetime
    allocated_by_user_id: int

    model_config = {"from_attributes": True}


class OrderKitItemRead(BaseModel):
    id: int
    order_id: int
    order_name: str
    kit_id: int
    kit_name: str
    product_id: int
    product_name: str
    product_hcp_code: str
    allocated_quantity: int
    allocated_at: datetime
    allocated_by_user_id: int

    model_config = {"from_attributes": True}


class AvailableKitRead(BaseModel):
    kit_id: int
    kit_name: str
    product_id: int
    product_name: str
    product_hcp_code: str
    quantity: int
    remaining_quantity: int
    is_complete: bool

    model_config = {"from_attributes": True}


class AllocateSelectedKitsRequest(BaseModel):
    kit_ids: list[int]


class AllocationCreatedItem(BaseModel):
    order_kit_id: int
    kit_id: int
    kit_name: str
    allocated_quantity: int


class AllocationSummaryRead(BaseModel):
    order_id: int
    order_name: str
    order_quantity: int
    allocated_quantity_total: int
    remaining_to_allocate: int
    is_fully_allocated: bool
    allocations_created: list[AllocationCreatedItem]
    message: str