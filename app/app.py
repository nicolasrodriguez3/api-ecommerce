from fastapi import FastAPI
from app.products.routers import router as products_router
from app.core.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title="Ecommerce API")

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    # Incluir routers
    app.include_router(products_router)

    return app


app = create_app()
