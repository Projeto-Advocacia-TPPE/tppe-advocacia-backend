from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field("development", validation_alias="APP_ENV")
    api_v1_prefix: str = Field("/api/v1", validation_alias="API_V1_PREFIX")
    frontend_url: str = Field("http://localhost:5173", validation_alias="FRONTEND_URL")

    api_port: int = Field(8000, validation_alias="API_HOST_PORT")

    app_name: str = Field("Advocacia API", validation_alias="APP_NAME")
    app_version: str = Field("0.1.0", validation_alias="APP_VERSION")

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "advocacia_db"

    jwt_secret_key: str = Field("change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(60, validation_alias="JWT_EXPIRE_MINUTES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
