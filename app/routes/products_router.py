from fastapi import APIRouter

from app.schemas.product_schema import ProductCreate
from app.services.product_service import ProductService


router = APIRouter(prefix="/products", tags=["Products"])

service = ProductService()

@router.post("/")
async def create_product(product: ProductCreate):
    return service.create_product(product)


@router.get("/")
async def get_products(limit: int = 10, offset: int = 0):
    return service.get_products(limit, offset)