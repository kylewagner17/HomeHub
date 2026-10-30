from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://homehub:homehub@localhost:5432/homehub"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = "dev-only-change-me-32-chars-minimum!!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    fcm_server_key: str | None = None
    reminder_scheduler_enabled: bool = True
    reminder_scheduler_interval_seconds: int = 60


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
