from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    app_name: str = "OCR API"
    api_prefix: str = "/api"
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    tesseract_cmd: str | None = None
    tessdata_prefix: str | None = None
    poppler_path: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_allowed_origins_list(self) -> list[str]:
        """Parse allowed origins from string configuration."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated disk access."""

    return Settings()
