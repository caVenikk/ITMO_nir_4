from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router
from api.internal import router as internal_router
from config import get_settings
from db.database import close_db_connection, create_tables

# Получение настроек
settings = get_settings()


# Создаем контекстный менеджер для событий запуска/остановки
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы
    await create_tables()

    yield

    # Закрываем соединения при завершении
    await close_db_connection()


# Создание FastAPI приложения
app = FastAPI(
    title="Code Analyzer Metrics API",
    description="API for measuring performance of Python static code analyzers",
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
app.include_router(api_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")  # Добавляем внутренний маршрут


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
