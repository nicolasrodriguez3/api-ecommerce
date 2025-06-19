# from sqlalchemy.orm import Session, joinedload
# from typing import List
# from datetime import datetime, timezone
# from app.core import db_connection
# from app.users.models import User
# from app.users.schemas import UserCreate, UserResponse, UserUpdate
# from app.core.security import get_password_hash
# from app.core.exceptions import (
#     BadRequestException,
#     UnauthorizedException,
#     NotFoundException,
# )
# from .roles import RoleEnum

# db: Session = db_connection.session

# def create_user(user_data: UserCreate) -> UserResponse:
#     if db.query(User).filter(User.email == user_data.email).first():
#         raise BadRequestException("Email already registered")

#     try:
#         new_user = User(
#             email=user_data.email,
#             hashed_password=get_password_hash(user_data.password),
#             is_active=True,
#             role=RoleEnum.CUSTOMER,
#         )
        
#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user)
#         return UserResponse.model_validate(new_user)
#     except Exception as e:
#         db.rollback()
#         raise BadRequestException(f"Failed to create user: {str(e)}")


# def get_user(user_id: int, db: Session) -> UserResponse:
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise NotFoundException(f"User with id {user_id} not found")

#     return UserResponse(
#         id=user.id,
#         email=user.email,
#         is_active=user.is_active,
#         created_at=user.created_at,
#         updated_at=user.updated_at,
#         role=user.role,
#     )


# def get_users(skip: int = 0, limit: int = 100) -> List[UserResponse]:
#     users = (
#         db.query(User).offset(skip).limit(limit).all()
#     )
#     return [
#         UserResponse(
#             id=user.id,
#             email=user.email,
#             is_active=user.is_active,
#             created_at=user.created_at,
#             updated_at=user.updated_at,
#             role=user.role,
#         )
#         for user in users
#     ]


# def update_user(user_id: int, user_update: UserUpdate) -> UserResponse:
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if not db_user:
#         raise NotFoundException(f"User with id {user_id} not found")

#     update_data = user_update.model_dump(exclude_unset=True)

#     if "email" in update_data and update_data["email"] != db_user.email:
#         if (
#             db.query(User)
#             .filter(User.email == update_data["email"], User.id != user_id)
#             .first()
#         ):
#             raise BadRequestException(
#                 f"Email '{update_data['email']}' is already registered by another user."
#             )
#         db_user.email = update_data["email"]

#     if "is_active" in update_data:
#         del update_data["is_active"]
        
#     if "role" in update_data:
#         if update_data["role"] not in RoleEnum._value2member_map_:
#             raise BadRequestException(f"Invalid role: {update_data['role']}")
#         db_user.role = update_data["role"]

#     # Update timestamp
#     db_user.updated_at = datetime.now(timezone.utc)

#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return UserResponse.model_validate(db_user)


# def delete_user(user_id: int) -> None:
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if not db_user:
#         raise NotFoundException(f"User with id {user_id} not found")

#     db_user.is_active = False
#     db.commit()
#     return None



from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import setup_logger
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundError, AlreadyExistsError
from app.repositories.user import UserRepository
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
        *, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False
    ) -> List[UserResponse]:
        """
        Obtener lista de usuarios.
        
        Args:
            skip: Registros a saltar
            limit: Límite de registros
            active_only: Solo usuarios activos
            
        Returns:
            List[UserResponse]: Lista de usuarios
        """
        if active_only:
            db_users = await self.user_repo.get_active_users(skip=skip, limit=limit)
        else:
            db_users = await self.user_repo.get_multi(skip=skip, limit=limit)
        
        return [UserResponse.from_user(user) for user in db_users]
    
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
            if existing_user is not None and getattr(existing_user, "id", None) != user_id:
                raise AlreadyExistsError("User", "email", user_data.email)
            
        if user_data.roles:
            del user_data.roles
        
        # Actualizar usuario
        db_user = await self.user_repo.update(user_id, user_data.model_dump(exclude_unset=True))
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
    
