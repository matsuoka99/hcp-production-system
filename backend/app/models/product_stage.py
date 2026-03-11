from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, CheckConstraint
from app.db.session import Base

class ProductStage(Base):
    __tablename__ = "product_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "stage_id", name="uq_product_stages_product_stage"),
        UniqueConstraint("product_id", "sequence", name="uq_product_stages_product_sequence"),
        CheckConstraint("sequence > 0", name="ck_product_stages_sequence_positive"),
    )