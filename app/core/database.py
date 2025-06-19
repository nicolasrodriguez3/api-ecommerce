from typing import AsyncGenerator, Generator
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Configuración del engine según el tipo de base de datos
def create_database_engine() -> AsyncEngine:
    """Crear engine de base de datos con configuración optimizada."""
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        poolclass=NullPool,
        future=True,
    )


# Crear engine y session factory
engine = create_database_engine()
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


# Base para modelos
class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia para la base de datos.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Error en la sesión de base de datos: {e}")
            raise
        finally:
            await session.close()
