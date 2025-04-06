import datetime
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Task


async def create_task(
    db: AsyncSession,
    analyzer_name: str,
    repository_url: str,
    command_template: str = "{analyzer_cmd} .",
) -> Task:
    """Создает новую задачу анализа."""
    task_id = str(uuid.uuid4())
    task = Task(
        task_id=task_id,
        analyzer_name=analyzer_name,
        repository_url=repository_url,
        command_template=command_template,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: str) -> Task | None:
    """Получает задачу по ID."""
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    return result.scalars().first()


async def update_task_status(
    db: AsyncSession,
    task_id: str,
    status: str,
    error_message: str | None = None,
    metrics_file_path: str | None = None,
) -> Task | None:
    """Обновляет статус задачи."""
    update_values: dict[str, Any] = {"status": status}

    if status in ["completed", "failed"]:
        update_values["completed_at"] = datetime.datetime.now(tz=None)

    if error_message:
        update_values["error_message"] = error_message

    if metrics_file_path:
        update_values["metrics_file_path"] = metrics_file_path

    stmt = update(Task).where(Task.task_id == task_id).values(**update_values)
    await db.execute(stmt)
    await db.commit()

    return await get_task_by_id(db, task_id)


async def mark_metrics_downloaded(db: AsyncSession, task_id: str) -> Task | None:
    """Отмечает, что метрики были скачаны."""
    stmt = update(Task).where(Task.task_id == task_id).values(metrics_downloaded=True)
    await db.execute(stmt)
    await db.commit()

    return await get_task_by_id(db, task_id)
