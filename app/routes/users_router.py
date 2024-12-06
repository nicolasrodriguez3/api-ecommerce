from typing import List
from fastapi import APIRouter, Query
from typing_extensions import Annotated
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

service = UserService()

@router.get("/")
async def get_users(limit: Annotated[int, Query(ge=1, le=100)] = 10, offset: Annotated[int | None, Query(ge=0)] = None):
    return service.get_users(limit, offset)

@router.post("/")
async def create_user(user: UserCreate):
    return service.create_user(user)
