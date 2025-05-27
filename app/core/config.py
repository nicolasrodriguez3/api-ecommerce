from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Ecommerce API"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    database_url: str = "sqlite:///./ecommerce.db"
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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings() # type: ignore
