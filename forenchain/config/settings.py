from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = Field(
        default="postgresql://forenchain:changeme@localhost:5432/forenchain"
    )

    # Security — these must be changed before any deployment
    secret_key: str = Field(default="insecure-change-before-deploy-minimum-32-chars")
    hmac_secret: str = Field(default="insecure-hmac-change-before-deploy-minimum-32")

    # JWT
    access_token_expire_minutes: int = Field(default=15)
    jwt_algorithm: str = Field(default="HS256")

    # Application
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    app_version: str = Field(default="0.1.0")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_secrets(self) -> None:
        """Raise at startup if production is using default secrets."""
        if self.is_production:
            if "insecure" in self.secret_key or "insecure" in self.hmac_secret:
                raise ValueError(
                    "Production deployment detected with default secrets. "
                    "Set SECRET_KEY and HMAC_SECRET environment variables."
                )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_secrets()
    return settings
