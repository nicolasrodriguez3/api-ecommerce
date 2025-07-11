# from sqlalchemy import String
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from app.core.database import Base
# from datetime import datetime
# from sqlalchemy import DateTime
# from sqlalchemy.sql import func


# class Category(Base):
#     __tablename__ = "categories"

#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
#     products: Mapped[list["Product"]] = relationship(back_populates="category")
#     created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now(), onupdate=func.now()
#     )
