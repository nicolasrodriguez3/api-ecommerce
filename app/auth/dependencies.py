from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional
from app.core.database import get_session
from app.repositories.user import UserRepository
from app.core.security import verify_token
from app.models.user import User, UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_session)],
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
    user = await user_repo.get_by_id(user_id)
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
    db: Annotated[AsyncSession, Depends(get_session)],
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
    return await user_repo.get_by_id(user_id)


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependencia para requerir roles específicos.

    Uso:
    @router.get("/admin-only")
    async def admin_endpoint(user: User = Depends(require_roles([UserRole.ADMIN]))):
        pass
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not current_user.has_any_role(allowed_roles):
            role_names = [role.value for role in allowed_roles]
            user_roles = current_user.get_role_names()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Access denied. Insufficient permissions.",
                    "required_roles": role_names,
                    "user_roles": user_roles
                }
            )
        return current_user

    return role_checker


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependencia específica para requerir rol de administrador"""
    if not current_user.has_role(UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required.",
        )
    return current_user


async def require_owner(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependencia específica para requerir rol de owner"""
    if not current_user.has_role(UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Owner role required.",
        )
    return current_user


async def require_seller(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependencia específica para requerir rol de seller"""
    if not current_user.has_role(UserRole.SELLER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Seller role required.",
        )
    return current_user


# Tipos anotados para facilitar el uso
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
CurrentAdmin = Annotated[User, Depends(require_admin)]
CurrentOwner = Annotated[User, Depends(require_owner)]
CurrentSeller = Annotated[User, Depends(require_seller)]


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
        return bool(
            current_user.has_role(UserRole.ADMIN) and current_user.id != target_user_id
        )
