from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderStageEntryCreate(BaseModel):
    product_stage_id: int = Field(..., gt=0, description="ID da etapa do produto")
    quantity: int = Field(..., gt=0, description="Quantidade lançada nesta operação")
    description: str | None = Field(default=None, description="Observação opcional")
    performed_at: datetime = Field(..., description="Momento em que a atividade foi executada")


class OrderStageEntryUpdate(BaseModel):
    quantity: int | None = Field(default=None, gt=0, description="Nova quantidade do lançamento")
    description: str | None = Field(default=None, description="Nova observação")
    performed_at: datetime | None = Field(default=None, description="Novo momento de execução")


class OrderStageEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_stage_id: int
    quantity: int
    description: str | None
    performed_at: datetime
    created_at: datetime
    created_by_user_id: int


class OrderStageSummary(BaseModel):
    product_stage_id: int
    stage_id: int
    stage_name: str
    sequence: int
    quantity_completed: int
    completed_percent: float


class OrderProductionProgressResponse(BaseModel):
    order_id: int
    order_name: str
    order_quantity: int

    # Quantidade concluída real do pedido, baseada na última etapa.
    completed_quantity: int

    # Percentual concluído real do pedido, baseado na última etapa.
    completed_percent: float

    # Percentual global do fluxo produtivo, considerando a soma das etapas.
    overall_progress_percent: float

    is_ready_to_close: bool
    stages: list[OrderStageSummary]