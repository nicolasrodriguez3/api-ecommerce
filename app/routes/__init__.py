from fastapi import APIRouter
from .users_router import router as users_router
from .products_router import router as products_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(products_router)
