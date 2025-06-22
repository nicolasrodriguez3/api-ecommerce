from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, UserRole


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: UserRole) -> Optional[Role]:
        """Obtener rol por nombre"""
        result = await self.db.execute(select(Role).filter(Role.name == name))
        return result.scalar_one_or_none()

    async def get_or_create(
        self, name: UserRole, description: str | None = None
    ) -> Role:
        """Obtener rol existente o crear uno nuevo"""
        role = await self.get_by_name(name)
        if not role:
            role = Role(name=name, description=description)
            self.db.add(role)
            await self.db.flush()
        return role

    async def create_default_roles(self):
        """Crear roles por defecto si no existen"""
        for role_name in UserRole:
            await self.get_or_create(role_name)
        await self.db.commit()

    async def get_all(self) -> List[Role]:
        stmt = select(Role)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
