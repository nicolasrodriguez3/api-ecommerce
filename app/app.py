from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.core.database import Base, engine, get_db
from app.roles.init import init_roles
from app.products.router import router as products_router
from app.categories.router import router as categories_router
from app.stock.router import router as stock_router
from app.users.router import router as users_router
from app.roles.router import router as roles_router
from app.auth.router import router as auth_router
from app.orders.router import router as orders_router


# Crear tablas
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    init_roles(db)
    yield


app = FastAPI(title="Ecommerce API", lifespan=lifespan)


# Routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(stock_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(orders_router)


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
