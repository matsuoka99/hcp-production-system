from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, String, DateTime
from datetime import datetime
from app.db.session import Base


class OrderStageEntry(Base):
    __tablename__ = "order_stage_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)

    product_stage_id: Mapped[int] = mapped_column(
        ForeignKey("product_stages.id"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    description: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    order = relationship("Order")
    product_stage = relationship("ProductStage")
    created_by_user = relationship("User")