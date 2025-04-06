from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from config import get_settings
from db.models import Base

# Получение настроек
settings = get_settings()

# Инициализация базы данных
engine = create_async_engine(settings.database_url, echo=settings.db_echo)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# Функции для управления жизненным циклом БД
async def create_tables():
    """Создает таблицы в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db_connection():
    """Закрывает соединение с базой данных"""
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД в эндпоинтах.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
