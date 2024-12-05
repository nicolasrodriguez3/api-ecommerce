from fastapi import APIRouter, HTTPException
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

service = UserService()

@router.get("/")
async def get_users():
    return {"users": ["user1", "user2", "user3"]}

@router.post("/")
async def create_user(user):
    return service.create(user)