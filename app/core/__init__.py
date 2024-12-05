from app.models.base_model import BaseModel
from .config import settings
from .db import DBConnection


database_connection = DBConnection(settings.DATABASE_URL)

def create_tables() -> None:
    BaseModel.metadata.create_all(bind=database_connection.engine)