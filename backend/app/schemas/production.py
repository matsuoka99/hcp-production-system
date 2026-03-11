from pydantic import BaseModel, Field
from datetime import datetime

class ProductionEntryCreate(BaseModel):
    order_id: int
    product_stage_id: int
    quantity: int = Field(gt=0)
    created_by_user_id: int
    description: str | None = None
    performed_at: datetime

class ProductionEntryRead(BaseModel):
    id: int
    order_id: int
    product_stage_id: int
    quantity: int
    created_by_user_id: int
    description: str | None
    performed_at: datetime

    model_config = {"from_attributes": True}