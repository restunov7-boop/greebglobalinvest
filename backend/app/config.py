from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="CORE Wine Club", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/core_wine_club",
        alias="DATABASE_URL",
    )
    jwt_secret: str = Field(default="change_me", alias="JWT_SECRET")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_sender_mode: str = Field(default="mock", alias="TELEGRAM_SENDER_MODE")
    telegram_real_send_scope: str = Field(default="pilot", alias="TELEGRAM_REAL_SEND_SCOPE")
    telegram_pilot_chat_id: str = Field(default="", alias="TELEGRAM_PILOT_CHAT_ID")
    telegram_pilot_telegram_user_id: str = Field(default="", alias="TELEGRAM_PILOT_TELEGRAM_USER_ID")
    telegram_api_base_url: str = Field(default="https://api.telegram.org", alias="TELEGRAM_API_BASE_URL")
    telegram_send_timeout_seconds: float = Field(default=10, alias="TELEGRAM_SEND_TIMEOUT_SECONDS")
    telegram_send_rate_limit_per_second: int = Field(default=20, alias="TELEGRAM_SEND_RATE_LIMIT_PER_SECOND")
    telegram_auth_max_age_seconds: int = Field(default=86400, alias="TELEGRAM_AUTH_MAX_AGE_SECONDS")
    dev_auth_enabled: bool = Field(default=True, alias="DEV_AUTH_ENABLED")
    dev_telegram_id: str = Field(default="100001", alias="DEV_TELEGRAM_ID")
    dev_telegram_username: str = Field(default="core_dev_user", alias="DEV_TELEGRAM_USERNAME")
    dev_telegram_first_name: str = Field(default="CORE", alias="DEV_TELEGRAM_FIRST_NAME")
    mobile_preview_enabled: bool = Field(default=False, alias="MOBILE_PREVIEW_ENABLED")
    access_token_expire_minutes: int = Field(default=10080, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cors_origins_raw: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]
        if self.is_mobile_preview_cors_enabled:
            origins.extend(["http://127.0.0.1:5173", "http://localhost:5173"])
        return list(dict.fromkeys(origins))

    @property
    def cors_origin_regex(self) -> str | None:
        if self.is_mobile_preview_cors_enabled:
            return r"https://[a-zA-Z0-9-]+\.trycloudflare\.com"
        return None

    @property
    def is_mobile_preview_cors_enabled(self) -> bool:
        return self.app_env != "production" and self.dev_auth_enabled and self.mobile_preview_enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
