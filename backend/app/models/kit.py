from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.db.session import Base


class Kit(Base):
    __tablename__ = "kits"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    description: Mapped[str | None] = mapped_column(String, nullable=True)

    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    client = relationship("Client")
    product = relationship("Product")
    
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    closed_by_user = relationship("User", foreign_keys=[closed_by_user_id])