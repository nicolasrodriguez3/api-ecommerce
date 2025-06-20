from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Ecommerce API"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    
    # Environment settings
    environment: str = "development" # Options: development, production, testing
    debug: bool = True  # Enable or disable debug mode
    log_level: str = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./ecommerce.db"
    database_echo: bool = False  # Enable SQLAlchemy echo for debugging
    
    # Security settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cloudinary settings
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    
    @property
    def cloudinary_url(self) -> str:
        return f"cloudinary://{self.cloudinary_api_key}:{self.cloudinary_api_secret}@{self.cloudinary_cloud_name}"

    @property
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings() # type: ignore
