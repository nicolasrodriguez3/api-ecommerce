from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], ABC):
    """Repositorio base con operaciones CRUD genéricas."""
    
    def __init__(self, db: Session, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model
    
    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Crear un nuevo registro."""
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        """Obtener registro por ID."""
        stmt = select(self.model).where(self.model.id == obj_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Obtener múltiples registros con paginación."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def update(self, obj_id: int, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Actualizar registro."""
        # Filtrar valores None
        update_data = {k: v for k, v in obj_data.items() if v is not None}
        
        if not update_data:
            return self.get_by_id(obj_id)
        
        stmt = update(self.model).where(self.model.id == obj_id).values(**update_data)
        result = self.db.execute(stmt)
        
        if result.rowcount == 0:
            return None
        
        self.db.commit()
        return self.get_by_id(obj_id)
    
    def delete(self, obj_id: int) -> bool:
        """Eliminar registro."""
        stmt = delete(self.model).where(self.model.id == obj_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def count(self) -> int:
        """Contar total de registros."""
        stmt = select(func.count(self.model.id))
        result = self.db.execute(stmt).scalar()
        return result if result is not None else 0
        
    
    def exists(self, obj_id: int) -> bool:
        """Verificar si existe un registro."""
        stmt = select(func.count(self.model.id)).where(self.model.id == obj_id)
        result = self.db.execute(stmt).scalar()
        return result > 0 if result is not None else False
        