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
from typing import Optional
from app.core.database import get_db
from app.users.repository import UserRepository
from app.auth.utils import verify_token
from app.users.models import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia que obtiene el usuario autenticado actual
    Uso: current_user: User = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verificar token
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception
    
    # Buscar usuario en BD
    user_repo = UserRepository(db)
    user_id = int(user_id)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que obtiene el usuario autenticado y activo
    Uso: current_user: User = Depends(get_current_active_user)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario inactivo"
        )
    return current_user

# def get_current_verified_user(
#     current_user: User = Depends(get_current_active_user)
# ) -> User:
#     """
#     Dependencia que obtiene el usuario autenticado, activo y verificado
#     Uso: current_user: User = Depends(get_current_verified_user)
#     """
#     if not current_user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Usuario no verificado"
#         )
#     return current_user

# Función opcional para obtener usuario sin lanzar excepción
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependencia que obtiene el usuario autenticado opcionalmente
    Retorna None si no hay token o es inválido
    """
    if not credentials:
        return None
    
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        return None
    
    user_repo = UserRepository(db)
    user_id = int(user_id)
    return user_repo.get_by_id(user_id)