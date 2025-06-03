from fastapi import APIRouter
from app.roles import service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
def list_roles() -> list[str]:
    return service.get_roles()
