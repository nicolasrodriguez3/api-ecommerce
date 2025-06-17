from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings


from app.core.database import Base, engine
from app.core.exceptions import AppException

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
from app.api.v1.categories import router as categories_router
from app.core.logger import setup_logger


# Crear tablas
Base.metadata.create_all(bind=engine)

settings = get_settings()
logger = setup_logger(__name__, level=settings.log_level)


app = FastAPI(title="Ecommerce API")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Manejadores de excepciones
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Manejar excepciones de la aplicación."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Manejar errores de validación."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Manejar errores de SQLAlchemy."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Ejecutar al iniciar la aplicación."""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecutar al cerrar la aplicación."""
    logger.info("Shutting down application")


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
