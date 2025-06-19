# app/core/init.py
from app.core.database import engine, Base, async_session
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

async def init_db():
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear usuario admin si no existe
    async with async_session() as session:
        await create_default_admin(session)


async def create_default_admin(session: AsyncSession):
    result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
    user = result.scalar_one_or_none()

    if user is None:
        new_user = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            is_active=True,
        )
        session.add(new_user)
        await session.commit()
        print("✅ Usuario administrador creado.")
    else:
        print("ℹ️ Usuario administrador ya existe.")
