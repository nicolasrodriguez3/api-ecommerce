from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundException
from app.products.router import router as products_router
from app.categories.router import router as categories_router
from app.core.database import Base, engine


app = FastAPI(title="Ecommerce API")

# Crear tablas
Base.metadata.create_all(bind=engine)

# Incluir routers
app.include_router(products_router)
app.include_router(categories_router)


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
