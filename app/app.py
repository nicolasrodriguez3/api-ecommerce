from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.database import Base, engine
from app.products.router import router as products_router
from app.categories.router import router as categories_router
from app.stock.router import router as stock_router


app = FastAPI(title="Ecommerce API")

# Crear tablas
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(stock_router)


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
