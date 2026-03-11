from pydantic import BaseModel, Field

class ProductStageCreate(BaseModel):
    product_id: int
    stage_id: int
    sequence: int = Field(gt=0)

class ProductStageRead(BaseModel):
    id: int
    product_id: int
    stage_id: int
    sequence: int

    model_config = {"from_attributes": True}