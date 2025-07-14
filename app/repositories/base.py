from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, update, delete, func
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], ABC):
    """Repositorio base con operaciones CRUD genéricas."""

    def __init__(self, db: AsyncSession, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Crear un nuevo registro."""
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        """Obtener entidad por ID (excluyendo soft deleted)."""
        stmt = select(self.model).where(self.model.id == obj_id)
        # Excluir soft deleted solo si el modelo tiene el atributo 'is_deleted'
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(getattr(self.model, "is_deleted") == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Obtener múltiples registros con filtros y paginación."""
        stmt = select(self.model)

        if filters:
            for key, value in filters.items():
                stmt = stmt.where(getattr(self.model, key) == value)
        if order_by:
            stmt = stmt.order_by(getattr(self.model, order_by))

        stmt = stmt.offset(skip).limit(limit)
        # Ejecutar la consulta y devolver los resultados
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, obj_id: int, obj_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Actualizar registro."""
        # Filtrar valores None
        update_data = {k: v for k, v in obj_data.items() if v is not None}

        if not update_data:
            return await self.get_by_id(obj_id)

        stmt = update(self.model).where(self.model.id == obj_id).values(**update_data)
        result = await self.db.execute(stmt)

        if result.rowcount == 0:
            return None

        await self.db.commit()
        return await self.get_by_id(obj_id)

    async def delete(self, obj_id: int) -> bool:
        """Eliminar entidad (hard delete)."""
        stmt = delete(self.model).where(self.model.id == obj_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def soft_delete(self, obj_id: int) -> bool:
        """Eliminar entidad (soft delete)."""
        if not hasattr(self.model, "is_deleted"):
            # Si el modelo no soporta soft delete, retornar False
            return False

        stmt = (
            update(self.model)
            .where(
                and_(
                    self.model.id == obj_id, getattr(self.model, "is_deleted") == False
                )
            )
            .values(is_deleted=True, updated_at=func.now())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def count(self, filters={}) -> int:
        """Contar entidades."""
        stmt = select(func.count(self.model.id))
        if filters:
            for key, value in filters.items():
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.db.execute(stmt)
        result = result.scalar()
        return result if result is not None else 0

    async def exists(self, entity_id: int) -> bool:
        """Verificar si existe una entidad."""
        stmt = select(self.model.id).where(self.model.id == entity_id)

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(getattr(self.model, "is_deleted") == False)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
