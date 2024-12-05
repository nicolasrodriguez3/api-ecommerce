from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_CONN: str

    @property
    def DATABASE_URL(self) -> str:
        return self.DB_CONN


settings = Settings()  # type: ignore
