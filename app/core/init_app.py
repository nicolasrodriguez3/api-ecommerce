from fastapi import FastAPI
from app.products.routers import router as products_router
from app.core.database import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Ecommerce API")

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    # Incluir routers
    app.include_router(products_router)

    # Eventos de inicio / apagado (opcional)
    @app.on_event("startup")
    async def startup_event():
        print("🚀 Aplicación iniciada")

    @app.on_event("shutdown")
    async def shutdown_event():
        print("🛑 Aplicación detenida")

    return app
