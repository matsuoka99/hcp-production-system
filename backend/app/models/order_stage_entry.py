from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class OrderStageEntry(Base):
    __tablename__ = "order_stage_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Pedido ao qual este lançamento pertence.
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
    )

    # Etapa do roteiro do produto à qual este lançamento pertence.
    product_stage_id: Mapped[int] = mapped_column(
        ForeignKey("product_stages.id"),
        nullable=False,
    )

    # Quantidade informada neste lançamento.
    # Este campo representa um DELTA, não um valor acumulado.
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Observação opcional do operador/supervisor.
    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Data/hora em que a atividade foi de fato executada no chão de fábrica.
    performed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # Data/hora de criação do registro no sistema.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Usuário que registrou o lançamento.
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    order = relationship("Order")
    product_stage = relationship("ProductStage")
    created_by_user = relationship("User")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_stage_entries_quantity_positive"),
    )