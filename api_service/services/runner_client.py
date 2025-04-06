from typing import Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.operations import update_task_status

settings = get_settings()


async def start_analysis(
    task_id: str,
    analyzer_name: str,
    repository_url: str,
    command_template: str,
    db: AsyncSession,
) -> None:
    """
    Отправляет запрос на запуск анализа в Runner сервис.
    Обновляет статус задачи в БД.
    """
    url = f"{settings.runner_service_url}/tasks"
    payload = {
        "task_id": task_id,
        "analyzer_name": analyzer_name,
        "repository_url": repository_url,
        "command_template": command_template,
        "iterations": 100,  # Количество итераций для замеров
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:  # Увеличенный таймаут
            response = await client.post(url, json=payload)
            response.raise_for_status()

        # Обновляем статус задачи
        await update_task_status(db, task_id, "running")
    except Exception as e:
        # В случае ошибки обновляем статус на failed
        await update_task_status(db, task_id, "failed", str(e))
        raise


async def get_metrics_file(task_id: str) -> Tuple[bytes, str]:
    """
    Получает файл с метриками от Runner сервиса.
    Запрашивает удаление ресурсов после скачивания.

    Returns:
        Tuple[bytes, str]: Содержимое файла и MIME-тип
    """
    url = f"{settings.runner_service_url}/tasks/{task_id}/metrics"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

        # Запрашиваем очистку после получения файла
        cleanup_url = f"{settings.runner_service_url}/tasks/{task_id}/cleanup"
        await client.post(cleanup_url)

        return response.content, response.headers.get("content-type", "text/csv")


async def cancel_analysis(task_id: str) -> bool:
    """
    Отправляет запрос на отмену анализа в Runner сервис.

    Args:
        task_id: ID задачи для отмены

    Returns:
        bool: Успешность отмены
    """
    url = f"{settings.runner_service_url}/tasks/{task_id}/cancel"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url)
            return response.status_code == 200
    except Exception:
        return False
