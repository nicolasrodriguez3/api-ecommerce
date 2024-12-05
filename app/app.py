from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routes import api_router
from .core import database_connection, create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    if database_connection.connect():
        create_tables()
    # database_connection.connect()
    yield
    database_connection.disconnect()
# Crear tablas en la base de datos
# Base.metadata.create_all(bind=engine)


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
