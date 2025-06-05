# from typing import Annotated
# from fastapi import Depends, HTTPException, Path, status

# from app.core.security import get_current_user
# from app.users.models import User
# from app.users.roles import RoleEnum


# def require_roles(*roles: RoleEnum):
#     def role_checker(
#         current_user: Annotated[User, Depends(get_current_user)],
#     ):
#         if current_user.role not in roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to perform this action",
#             )
#         return current_user

#     return role_checker

# def require_self_or_roles(*roles: RoleEnum, user_id_path_param: str = "user_id"):
#     def dependency(
#         target_user_id: int = Path(..., alias=user_id_path_param), # Use alias for flexibility
#         current_user: User = Depends(get_current_user)
#     ):
#         if current_user.id == target_user_id:
#             return current_user # User is accessing their own resource

#         # If not self, check if user has one of the specified roles
#         # This assumes User model has 'role' attribute which has a 'name' attribute (e.g. RoleEnum.admin.name)
#         if hasattr(current_user, 'role') and current_user.role and current_user.role in roles:
#             return current_user # User has a permitted role

#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to perform this action on this resource.",
#         )
#     return dependency

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from app.core.database import get_db
from app.repositories.user import UserRepository
from app.core.security import verify_token
from app.models.user import User, UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Dependencia que obtiene el usuario autenticado actual
    Uso: current_user: Annotated[User, Depends(get_current_user)]
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verificar token
    token_data = verify_token(credentials.credentials)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    # Buscar usuario en BD
    user_repo = UserRepository(db)
    user_id = int(token_data.user_id)
    user = await user_repo.get(user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependencia que obtiene el usuario autenticado y activo
    Uso: current_user: Annotated[User, Depends(get_current_active_user)]
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )
    return current_user


# async def get_current_verified_user(
#     current_user: Annotated[User, Depends(get_current_active_user)]
# ) -> User:
#     """
#     Dependencia que obtiene el usuario autenticado, activo y verificado
#     Uso: current_user: Annotated[User, Depends(get_current_verified_user)]
#     """
#     if not current_user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Usuario no verificado"
#         )
#     return current_user


# Función opcional para obtener usuario sin lanzar excepción
async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    """
    Dependencia que obtiene el usuario autenticado opcionalmente
    Retorna None si no hay token o es inválido
    """
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials)
    if token_data is None or token_data.user_id is None:
        return None

    user_repo = UserRepository(db)
    user_id = int(token_data.user_id)
    return await user_repo.get(user_id)


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependencia para requerir roles específicos.

    Uso:
    @router.get("/admin-only")
    async def admin_endpoint(user: User = Depends(require_roles([UserRole.ADMIN]))):
        pass
    """

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_any_role(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}",
            )
        return current_user

    return role_checker

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependencia específica para requerir rol de administrador"""
    if not current_user.has_role(UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user


# Tipos anotados para facilitar el uso
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]


# Funciones helper para verificar permisos
class PermissionChecker:
    """Clase helper para verificar permisos complejos"""
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """Verificar si el usuario puede gestionar otros usuarios"""
        return user.has_any_role([UserRole.ADMIN, UserRole.OWNER])
    
    @staticmethod
    def can_view_user(current_user: User, target_user_id: int) -> bool:
        """Verificar si el usuario puede ver información de otro usuario"""
        # Los admins y owners pueden ver cualquier usuario
        if current_user.has_any_role([UserRole.ADMIN, UserRole.OWNER]):
            return True
        # Los usuarios pueden ver su propia información
        return bool(current_user.id == target_user_id)
    
    @staticmethod
    def can_edit_user(current_user: User, target_user_id: int) -> bool:
        """Verificar si el usuario puede editar información de otro usuario"""
        # Solo admins pueden editar otros usuarios
        if current_user.has_role(UserRole.ADMIN):
            return True
        # Los usuarios pueden editar su propia información
        return bool(current_user.id == target_user_id)
    
    @staticmethod
    def can_delete_user(current_user: User, target_user_id: int) -> bool:
        """Verificar si el usuario puede eliminar otro usuario"""
        # Solo admins pueden eliminar usuarios y no pueden eliminarse a sí mismos
        return bool(current_user.has_role(UserRole.ADMIN) and 
                current_user.id != target_user_id)