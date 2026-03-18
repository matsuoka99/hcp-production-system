from datetime import date, datetime

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    name: str
    client_id: int
    product_id: int
    quantity: int = Field(gt=0)
    description: str | None = None
    delivery_date: date


class OrderUpdate(BaseModel):
    name: str | None = None
    client_id: int | None = None
    product_id: int | None = None
    quantity: int | None = Field(default=None, gt=0)
    completed_quantity: int | None = Field(default=None, ge=0)
    description: str | None = None
    delivery_date: date | None = None
    is_active: bool | None = None


class OrderRead(BaseModel):
    id: int
    name: str
    client_id: int
    product_id: int
    quantity: int
    completed_quantity: int
    created_by_user_id: int | None = None
    description: str | None
    delivery_date: date
    is_active: bool

    # Campos derivados de alocação.
    allocated_quantity_total: int
    remaining_to_allocate: int
    is_fully_allocated: bool

    # Campos de fechamento/auditoria.
    created_at: datetime | None = None
    closed_at: datetime | None = None
    closed_by_user_id: int | None = None

    # Campo derivado para apoiar a tela de finalização.
    is_ready_to_finalize: bool

    model_config = {"from_attributes": True}