from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Ecommerce API"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    database_url: str = "sqlite:///./ecommerce.db"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
