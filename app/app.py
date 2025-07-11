from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.config import get_settings


from app.core.database import Base, engine
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import (
    EXCEPTION_STATUS_MAP,
    AppException,
    app_exception_handler,
)

# from app.products.router import router as products_router
# from app.categories.router import router as categories_router
# from app.stock.router import router as stock_router
# from app.users.router import router as users_router
# from app.roles.router import router as roles_router
# from app.auth.router import router as auth_router
# from app.orders.router import router as orders_router
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.products2 import router as products2_router
from app.api.v1.categories import router as categories_router
from app.core.init_db import init_db
from app.core.logger import setup_logger


# Crear tablas
# Base.metadata.create_all(bind=engine)

settings = get_settings()
logger = setup_logger(__name__, level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info(f"🚀 Starting {settings.app_name} v{settings.version}")
        logger.info(f"📦 Environment: {settings.environment}")
        logger.info(f"🗄️ Database URL: {settings.database_url}")

        await init_db()
        logger.info("✅ Database initialization completed")

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down application...")


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Manejadores de excepciones
register_exception_handlers(app)


# Routers
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)


# Endpoints de salud
@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint de verificación de salud."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
    }
