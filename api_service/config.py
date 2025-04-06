import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

print("os.environ.get('ENV')", os.environ.get("ENV"))


class Settings(BaseSettings):
    # Основные настройки
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS настройки
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # База данных
    database_url: str = "sqlite+aiosqlite:///./analyzer.db"
    db_echo: bool = False

    # Runner сервис
    runner_service_url: str = "http://runner:8080"

    # Таймауты
    request_timeout: int = 30

    model_config = SettingsConfigDict(
        env_file=".env.development" if os.environ.get("ENV") != "production" else ".env.production",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Синглтон для настроек
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Фабрика настроек для создания и получения настроек приложения.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
