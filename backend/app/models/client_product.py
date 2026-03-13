from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint

from app.db.session import Base


class ClientProduct(Base):
    __tablename__ = "client_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    client = relationship("Client", back_populates="client_products")
    product = relationship("Product", back_populates="client_products")

    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "product_id",
            name="uq_client_products_client_product",
        ),
    )