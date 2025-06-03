# from fastapi import HTTPException, status


# class NotFoundException(HTTPException):
#     def __init__(self, detail: str = "Resource not found"):
#         super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# class ConflictException(HTTPException):
#     def __init__(self, detail: str = "Conflict"):
#         super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


# class BadRequestException(HTTPException):
#     def __init__(self, detail: str = "Bad request"):
#         super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# class UnauthorizedException(HTTPException):
#     def __init__(self, detail: str = "Unauthorized"):
#         super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


# class ForbiddenException(HTTPException):
#     def __init__(self, detail: str = "Forbidden"):
#         super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class AppException(Exception):
    """Excepción base de la aplicación."""
    
    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Error cuando un recurso no se encuentra."""
    
    def __init__(self, resource: str, identifier: str | int) -> None:
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND")


class AlreadyExistsError(AppException):
    """Error cuando un recurso ya existe."""
    
    def __init__(self, resource: str, field: str, value: str) -> None:
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message, "ALREADY_EXISTS")


class ValidationError(AppException):
    """Error de validación de datos."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR")