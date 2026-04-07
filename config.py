from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "TAJ VPN Backend"
    environment: str = "development"
    database_url: str = f"sqlite:///{(BASE_DIR / 'vpn_backend.db').as_posix()}"
    public_base_url: str = "http://localhost:8000"
    allowed_origins: str = "*"

    enot_api_base: str = "https://api.enot.io"
    enot_shop_id: str = ""
    enot_api_key: str = ""
    enot_webhook_secret: str = ""
    enot_currency: str = "RUB"
    enot_success_url: str = "https://example.com/payment/success"
    enot_fail_url: str = "https://example.com/payment/fail"
    enot_expire_minutes: int = 30
    enot_hook_path: str = "/webhooks/enot"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or ["*"]

    @property
    def enot_hook_url(self) -> str:
        base = self.public_base_url.rstrip("/")
        path = self.enot_hook_path if self.enot_hook_path.startswith("/") else f"/{self.enot_hook_path}"
        return f"{base}{path}"

    @field_validator("public_base_url", "enot_api_base", mode="before")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
