from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_WEAK_JWT_SECRETS = {"your-secret-key", "change-me", "secret"}
_MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    app_env: str = Field("development", validation_alias="APP_ENV")
    api_v1_prefix: str = Field("/api/v1", validation_alias="API_V1_PREFIX")
    frontend_url: str = Field("http://localhost:5173", validation_alias="FRONTEND_URL")
    frontend_url_alt: str = Field(
        "http://127.0.0.1:5173", validation_alias="FRONTEND_URL_ALT"
    )

    api_port: int = Field(8000, validation_alias="API_HOST_PORT")

    app_name: str = Field("Advocacia API", validation_alias="APP_NAME")
    app_version: str = Field("0.1.0", validation_alias="APP_VERSION")

    postgres_user: str = Field("postgres", validation_alias="POSTGRES_USER")
    postgres_password: str = Field("postgres", validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field("advocacia_db", validation_alias="POSTGRES_DB")

    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(60, validation_alias="JWT_EXPIRE_MINUTES")
    password_reset_expire_minutes: int = Field(
        30, validation_alias="PASSWORD_RESET_EXPIRE_MINUTES"
    )

    resend_api_key: str = Field(validation_alias="RESEND_API_KEY")
    resend_from_email: str = Field(
        "onboarding@resend.dev", validation_alias="RESEND_FROM_EMAIL"
    )

    lead_dedup_window_hours: int = Field(1, validation_alias="LEAD_DEDUP_WINDOW_HOURS")

    upload_dir: str = Field("uploads/media", validation_alias="UPLOAD_DIR")
    max_file_size_mb: int = Field(5, validation_alias="MAX_FILE_SIZE_MB")
    allowed_mime_types: list[str] = Field(
        default=["image/jpeg", "image/png"],
        validation_alias="ALLOWED_MIME_TYPES",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def strong_jwt_secret(cls, jwt_secret_key: str, info: ValidationInfo) -> str:
        if info.data.get("app_env") == "production" and (
            len(jwt_secret_key) < _MIN_JWT_SECRET_LENGTH
            or jwt_secret_key in _WEAK_JWT_SECRETS
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be at least "
                f"{_MIN_JWT_SECRET_LENGTH} chars and not a known default in production"
            )
        return jwt_secret_key

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
