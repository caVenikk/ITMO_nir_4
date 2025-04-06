import logging
import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router
from config import get_settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("runner")

# Получение настроек
settings = get_settings()


# Создаем контекстный менеджер для событий запуска/остановки
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем необходимые директории
    os.makedirs(settings.repos_dir, exist_ok=True)
    os.makedirs(settings.metrics_dir, exist_ok=True)

    # Компилируем Go-сборщик метрик
    logger.info("Компиляция Go-сборщика метрик...")
    try:
        subprocess.run(
            [
                settings.go_binary_path,
                "build",
                "-o",
                settings.compiled_collector_path,
                settings.metrics_collector_path,
            ],
            check=True,
        )
        logger.info("Компиляция успешно завершена")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка компиляции Go-сборщика: {e}")

    yield

    logger.info("Завершение работы runner сервиса")


# Создание FastAPI приложения
app = FastAPI(
    title="Code Analyzer Runner",
    description="Service for running code analysis tasks",
    version="1.0.0",
    lifespan=lifespan,
)

# Настройка CORS с использованием значений из конфигурации
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация маршрутов
app.include_router(api_router, prefix="")


# Эндпоинт для проверки состояния
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.host, port=settings.port, reload=settings.debug
    )
