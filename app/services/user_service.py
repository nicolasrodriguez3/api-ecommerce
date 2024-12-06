from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.core import database_connection
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate



class UserService:
    def __init__(self):
        self.db = database_connection.session

    def create_user(self, user: UserCreate):
        # Verificar si el correo ya existe
        existing_user = self.db.query(UserModel).filter(UserModel.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Crear nuevo usuario
        hashed_password = "hash_password(user.password)"
        new_user = UserModel(
            name=user.name,
            email=user.email,
            password_hash=hashed_password,
        )
        self.db.add(new_user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        self.db.refresh(new_user)
        return new_user
    
    
    def get_users(self, limit, offset):
        users = self.db.query(UserModel).limit(limit).offset(offset).all()
        return users