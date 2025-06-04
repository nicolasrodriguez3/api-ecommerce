from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configuración del engine según el tipo de base de datos
def create_database_engine() -> Engine:
    """Crear engine de base de datos con configuración optimizada."""
    connect_args = {}
    poolclass = None
    
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool
        
        # Habilitar foreign keys en SQLite
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    return create_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args=connect_args,
        poolclass=poolclass,
        pool_pre_ping=True,  # Verificar conexiones antes de usar
    )


# Crear engine y session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    """
    Dependencia para la base de datos.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()  # Revertir cambios en caso de error
        logger.error(f"Error en la sesión de base de datos: {e}")
        raise
    finally:
        db.close()  # Cerrar la sesión al finalizar
