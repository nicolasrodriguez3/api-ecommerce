from fastapi import FastAPI
from app.products.router import router as products_router
from app.categories.router import router as categories_router
from app.core.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title="Ecommerce API")

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    # Incluir routers
    app.include_router(products_router)
    app.include_router(categories_router)

    return app


app = create_app()
