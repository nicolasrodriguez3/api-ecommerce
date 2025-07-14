from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import setup_logger
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundError, AlreadyExistsError
from app.models.user import UserRole
from app.repositories.user import UserRepository
from app.schemas.common import PaginatedResponse, PaginationParams, PaginationRequest
from app.schemas.user import UserCreate, UserUpdate, UserResponse


logger = setup_logger(__name__)


class UserService:
    """Servicio de usuarios con lógica de negocio."""

    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Crear un nuevo usuario.

        Args:
            user_data: Datos del usuario a crear

        Returns:
            UserResponse: Usuario creado

        Raises:
            AlreadyExistsError: Si el email ya existe
        """
        logger.info(f"Creating user with email: {user_data.email}")

        # Validar email único
        if await self.user_repo.get_by_email(user_data.email):
            raise AlreadyExistsError("User", "email", user_data.email)

        # Validar roles si se proporcionan
        if user_data.roles:
            for role_name in user_data.roles:
                if role_name not in UserRole:
                    raise ValueError(f"Invalid role: {role_name}")

        # Crear usuario
        hashed_password = get_password_hash(user_data.password)
        del user_data.password

        db_user = await self.user_repo.create_user(user_data, hashed_password)
        logger.info(f"User created successfully with ID: {db_user.id}")

        return UserResponse.from_user(db_user)

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """
        Obtener usuario por ID.

        Args:
            user_id: ID del usuario

        Returns:
            UserResponse: Usuario encontrado

        Raises:
            NotFoundError: Si el usuario no existe
        """
        db_user = await self.user_repo.get_by_id(user_id)
        if not db_user:
            raise NotFoundError("User", user_id)

        return UserResponse.from_user(db_user)

    async def get_users(
        self,
        pagination_request: PaginationRequest,
        active_only: bool = False,
    ) -> PaginatedResponse[UserResponse]:
        """
        Obtener lista de usuarios.

        Args:
            active_only: Solo usuarios activos

        Returns:
            PaginatedResponse[UserResponse]: Lista de usuarios
        """
        pagination = PaginationParams.from_request(pagination_request)

        if active_only:
            filters = {"is_active": True}
        else:
            filters = {}
            
        db_users = await self.user_repo.get_users(
                offset=pagination.offset, limit=pagination.limit,
                filters=filters,
            )

        # TODO contar los elementos segun el filtro
        total_elements = await self.user_repo.count(filters=filters)

        data = [UserResponse.from_user(user) for user in db_users]
        return PaginatedResponse(
            data=data,
            total_elements=total_elements,
            page=pagination_request.page,
            per_page=pagination_request.per_page,
        )

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """
        Actualizar usuario.

        Args:
            user_id: ID del usuario
            user_data: Datos a actualizar

        Returns:
            UserResponse: Usuario actualizado

        Raises:
            NotFoundError: Si el usuario no existe
            AlreadyExistsError: Si el email ya existe
        """
        logger.info(f"Updating user with ID: {user_id}")

        # Verificar que el usuario existe
        if not await self.user_repo.exists(user_id):
            raise NotFoundError("User", user_id)

        # Validar email único si se está actualizando
        if user_data.email:
            existing_user = await self.user_repo.get_by_email(user_data.email)
            if (
                existing_user is not None
                and getattr(existing_user, "id", None) != user_id
            ):
                raise AlreadyExistsError("User", "email", user_data.email)

        if user_data.roles:
            del user_data.roles

        # Actualizar usuario
        db_user = await self.user_repo.update(
            user_id, user_data.model_dump(exclude_unset=True)
        )
        logger.info(f"User updated successfully. ID: {user_id}")

        return UserResponse.from_user(db_user)

    async def delete_user(self, user_id: int) -> None:
        """
        Eliminar usuario.

        Args:
            user_id: ID del usuario

        Raises:
            NotFoundError: Si el usuario no existe
        """
        logger.info(f"Deleting user with ID: {user_id}")

        if not await self.user_repo.delete(user_id):
            raise NotFoundError("User", user_id)

        logger.info(f"User deleted successfully: {user_id}")
