from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.dependencies import get_user_service
from app.auth.dependencies import get_current_user
from app.core.exceptions import NotFoundError, AlreadyExistsError, ValidationError
from app.users.schemas import UserCreate, UserUpdate, UserResponse
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario",
    description="Obtiene un usuario por su ID",
    dependencies=[Depends(get_current_user)]
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Obtener usuario por ID."""
    try:
        return user_service.get_user_by_id(user_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Obtiene una lista paginada de usuarios"
)
async def get_users(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    active_only: bool = Query(False, description="Solo usuarios activos"),
    user_service: UserService = Depends(get_user_service)
) -> List[UserResponse]:
    """Obtener lista de usuarios."""
    return user_service.get_users(skip=skip, limit=limit, active_only=active_only)