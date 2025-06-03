from app.core.config import get_settings
from app.core.database import DatabaseConnection

settings = get_settings()

db_connection = DatabaseConnection(settings.database_url)

