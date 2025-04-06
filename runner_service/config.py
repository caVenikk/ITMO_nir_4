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
    port: int = 8080

    # CORS настройки
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Директории для данных
    data_dir: str = "/app/data"
    repos_dir: str = "/app/data/repos"
    metrics_dir: str = "/app/data/metrics"

    # Настройки анализатора
    go_binary_path: str = "/usr/local/go/bin/go"
    metrics_collector_path: str = "/app/metrics_collector.go"
    compiled_collector_path: str = "/app/metrics_collector"

    # Таймауты
    clone_timeout: int = 300  # 5 минут на клонирование репозитория
    install_timeout: int = 300  # 5 минут на установку пакета
    analyze_timeout: int = 3600  # 1 час на выполнение анализа

    api_service_url: str = "http://api:8000/api/v1"
    api_request_timeout: int = 10

    # Ограничения
    max_concurrent_tasks: int = 2  # Максимальное количество одновременных задач

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
