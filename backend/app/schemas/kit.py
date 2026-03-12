from pydantic import BaseModel, Field
from datetime import datetime

class KitCreate(BaseModel):
    name: str
    product_id: int
    quantity: int = Field(gt=0)
    created_by_user_id: int
    description: str | None = None

class KitRead(BaseModel):
    id: int
    name: str
    product_id: int
    quantity: int
    remaining_quantity: int
    created_by_user_id: int
    description: str | None
    is_complete: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}