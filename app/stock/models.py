# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import ForeignKey, String, DateTime
# from datetime import datetime
# from app.core.database import Base


# class StockHistory(Base):
#     __tablename__ = "stock_history"

#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
#     quantity: Mapped[int]
#     reason: Mapped[str]
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

#     product: Mapped["Product"] = relationship("Product", back_populates="stock_history")
