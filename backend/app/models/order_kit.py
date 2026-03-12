from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, DateTime
from datetime import datetime
from app.db.session import Base


class OrderKit(Base):
    __tablename__ = "order_kits"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    kit_id: Mapped[int] = mapped_column(ForeignKey("kits.id"), nullable=False)

    allocated_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    allocated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    allocated_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    order = relationship("Order")
    kit = relationship("Kit")
    allocated_by_user = relationship("User")

    __table_args__ = (
        UniqueConstraint("order_id", "kit_id", name="uq_order_kits_order_kit"),
    )