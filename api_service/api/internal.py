from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import TaskStatusUpdate
from db.database import get_db
from db.operations import get_task_by_id, update_task_status

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/tasks/{task_id}/status", status_code=status.HTTP_200_OK)
async def update_task_status_internal(
    task_id: str, status_update: TaskStatusUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Внутренний эндпоинт для обновления статуса задачи от Runner сервиса.
    Не предназначен для использования клиентами.
    """
    # Проверяем существование задачи
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Обновляем статус задачи
    await update_task_status(
        db=db,
        task_id=task_id,
        status=status_update.status,
        error_message=status_update.error,
        metrics_file_path=status_update.metrics_file,
    )

    return {"status": "updated", "task_id": task_id}
