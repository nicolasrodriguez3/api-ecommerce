from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.dependencies import get_user_service
from app.auth.dependencies import (
    CurrentUser,
    PermissionChecker,
    get_current_user,
    require_admin,
)
from app.core.exceptions import NotFoundError, AlreadyExistsError, ValidationError
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Obtiene una lista paginada de usuarios",
)
async def get_users(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    active_only: bool = Query(False, description="Solo usuarios activos"),
    user_service: UserService = Depends(get_user_service),
) -> List[UserResponse]:
    """Obtener lista de usuarios."""
    return await user_service.get_users(skip=skip, limit=limit, active_only=active_only)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario actual",
    description="Obtiene los detalles del usuario autenticado",
)
async def get_current_user_details(
    current_user: CurrentUser,
) -> UserResponse:
    """Obtener detalles del usuario autenticado."""
    return UserResponse.from_user(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario",
    description="Obtiene un usuario por su ID",
    dependencies=[Depends(get_current_user)],
)
async def get_user(
    user_id: int, user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Obtener usuario por ID."""
    try:
        return await user_service.get_user_by_id(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario en el sistema",
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)
async def create_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Crear un nuevo usuario."""
    try:
        return await user_service.create_user(user_data)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Actualiza la información de un usuario específico",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Actualizar información de un usuario específico.

    Permisos:
    - Admins: pueden editar cualquier usuario incluyendo roles
    - Usuarios normales: solo pueden editar su propia información (excepto roles)
    """
    # Verificar permisos de edición
    if not PermissionChecker.can_edit_user(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only edit your own profile.",
        )

    # Solo admins pueden modificar roles
    if not current_user.has_role(UserRole.ADMIN) and user_data.roles is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify user roles",
        )

    updated_user = await user_service.update_user(user_id, user_data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return updated_user


# Endpoints específicos para gestión de roles


@router.put("/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: int,
    roles: List[UserRole],
    current_user: User = Depends(require_admin),  # Solo admins pueden modificar roles
    user_service: UserService = Depends(get_user_service),
):
    """
    Actualizar roles de un usuario específico. Solo administradores.
    """
    user_data = UserUpdate(roles=roles)

    updated_user = await user_service.update_user(user_id, user_data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return updated_user


@router.get("/by-role/{role}")
async def get_users_by_role(
    role: UserRole,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """
    Obtener usuarios por rol específico. Requiere rol de dueño o administrador.
    """
    users = await user_service.user_repo.get_users_by_role(role)

    return [UserResponse.from_user(user) for user in users]
