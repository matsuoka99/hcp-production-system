from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from app.db.session import Base


class OrderKit(Base):
    __tablename__ = "order_kits"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)

    kit_id: Mapped[int] = mapped_column(ForeignKey("kits.id"), nullable=False)

    allocated_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", "kit_id", name="uq_order_kits_order_kit"),
    )