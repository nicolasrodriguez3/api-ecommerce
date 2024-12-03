from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_users():
    return {"users": ["user1", "user2", "user3"]}

@router.post("/")
async def create_user():
    return {"message": "User created"}
