from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey
from app.db.session import Base


class OrderProgress(Base):
    __tablename__ = "order_progress"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)

    product_stage_id: Mapped[int] = mapped_column(
        ForeignKey("product_stages.id"),
        nullable=False
    )

    quantity_completed: Mapped[int] = mapped_column(Integer, default=0)

    order = relationship("Order")
    product_stage = relationship("ProductStage")