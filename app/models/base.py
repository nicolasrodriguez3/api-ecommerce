from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BaseModel(Base):
    """Modelo base con campos comunes."""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        default=None
    )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__} #{self.id}"
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    @classmethod
    def get_column_names(cls) -> list[str]:
        """Obtiene los nombres de las columnas del modelo."""
        return [column.name for column in cls.__table__.columns]
    