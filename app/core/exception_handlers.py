"""
Handlers para excepciones de la aplicación.

Este módulo contiene todos los handlers de excepciones que se registran en FastAPI.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.logger import setup_logger

from .exceptions import AppException, EXCEPTION_STATUS_MAP

logger = setup_logger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Manejar excepciones de la aplicación con códigos HTTP apropiados."""

    # Usar el mapeo para obtener el código HTTP correcto
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)

    # Log según severidad
    if status_code >= 500:
        logger.error(f"Server error: {exc.message}")
    else:
        logger.warning(f"Application error: {exc.message}")

    content = {"detail": exc.message, "code": exc.code}
    if exc.details:
        content["details"] = str(exc.details)

    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Manejar errores de validación."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "path": request.url.path,
        },
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Manejar errores de SQLAlchemy."""

    # Manejo especial para violaciones de unicidad
    if isinstance(exc, IntegrityError) and "unique constraint" in str(exc).lower():
        logger.warning(f"Unique constraint violation: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Resource already exists",
                "code": "UNIQUE_CONSTRAINT_VIOLATION",
            },
        )

    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred", "code": "DATABASE_ERROR"},
    )


def register_exception_handlers(app) -> None:
    """
    Registra todos los handlers de excepciones en la aplicación FastAPI.

    Args:
        app: Instancia de FastAPI
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
