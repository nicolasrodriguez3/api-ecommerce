from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.users.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user
