
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, UserRole

class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: UserRole) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, name: UserRole, description: str | None = None) -> Role:
        role = await self.get_by_name(name)
        if not role:
            role = Role(name=name, description=description)
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
        return role

    async def get_all(self) -> List[Role]:
        stmt = select(Role)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


