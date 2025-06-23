"""
Excepciones personalizadas de la aplicación.

Este módulo define las excepciones base y específicas usadas en toda la aplicación.
Incluye un handler global para convertir excepciones de dominio a respuestas HTTP.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Excepción base de la aplicación."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario para serialización."""
        result = {
            "message": self.message,
            "code": self.code,
        }
        if self.details:
            result["details"] = str(self.details)
        return result


class NotFoundError(AppException):
    """Error cuando un recurso no se encuentra."""
    
    def __init__(self, resource: str, identifier: str | int) -> None:
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message, 
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class AlreadyExistsError(AppException):
    """Error cuando un recurso ya existe."""
    
    def __init__(self, resource: str, field: str, value: str) -> None:
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(
            message=message, 
            code="RESOURCE_ALREADY_EXISTS",
            details={"resource": resource, "field": field, "value": value}
        )


class ValidationError(AppException):
    """Error de validación de datos."""
    
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message=message, 
            code="VALIDATION_ERROR",
            details=details
        )


class ConflictError(AppException):
    """Error cuando hay un conflicto con el estado actual del recurso."""

    def __init__(self, message: str = "Conflict error") -> None:
        super().__init__(message=message, code="CONFLICT_ERROR")


class AuthenticationError(AppException):
    """Error de autenticación."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    """Error de autorización."""
    
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class BusinessLogicError(AppException):
    """Error de lógica de negocio."""
    
    def __init__(self, message: str, operation: Optional[str] = None) -> None:
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=message, 
            code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class ExternalServiceError(AppException):
    """Error de servicio externo."""
    
    def __init__(self, service: str, message: str = "External service error") -> None:
        super().__init__(
            message=f"{service}: {message}", 
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


class DatabaseError(AppException):
    """Error de base de datos."""
    
    def __init__(self, message: str = "Database error", operation: Optional[str] = None) -> None:
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=message, 
            code="DATABASE_ERROR",
            details=details
        )


# Mapeo de excepciones a códigos HTTP
EXCEPTION_STATUS_MAP = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: status.HTTP_409_CONFLICT,
    ConflictError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_400_BAD_REQUEST,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    BusinessLogicError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler global para excepciones de la aplicación.
    
    Convierte las excepciones de dominio en respuestas HTTP apropiadas.
    """
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.to_dict(),
            "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None,
            "path": str(request.url.path),
        }
    )


# Funciones de conveniencia para casos comunes
def not_found(resource: str, identifier: str | int) -> NotFoundError:
    """Crea una excepción NotFoundError."""
    return NotFoundError(resource, identifier)


def already_exists(resource: str, field: str, value: str) -> AlreadyExistsError:
    """Crea una excepción AlreadyExistsError."""
    return AlreadyExistsError(resource, field, value)


def validation_error(message: str, field: Optional[str] = None) -> ValidationError:
    """Crea una excepción ValidationError."""
    return ValidationError(message, field)


def conflict_error(message: str) -> ConflictError:
    """Crea una excepción ConflictError."""
    return ConflictError(message)


def unauthorized(message: str = "Authentication required") -> AuthenticationError:
    """Crea una excepción AuthenticationError."""
    return AuthenticationError(message)


def forbidden(message: str = "Access denied") -> AuthorizationError:
    """Crea una excepción AuthorizationError."""
    return AuthorizationError(message)