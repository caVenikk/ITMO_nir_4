from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Response, status)
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (CancelTaskResponse, PyPISearchResponse, TaskCreate,
                        TaskResponse, TaskStatusResponse)
from db.database import get_db
from db.operations import (create_task, get_task_by_id,
                           mark_metrics_downloaded, update_task_status)
from services.pypi import search_pypi_packages
from services.runner_client import (cancel_analysis, get_metrics_file,
                                    start_analysis)

router = APIRouter()


@router.get("/pypi/search", response_model=PyPISearchResponse)
async def search_pypi(query: str = ""):
    """Поиск пакетов в PyPI по запросу."""
    packages = await search_pypi_packages(query)
    return {"packages": packages}


@router.post(
    "/analyze", response_model=TaskResponse, status_code=status.HTTP_201_CREATED
)
async def start_analyzer(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Запускает анализ репозитория с использованием выбранного инструмента.
    Возвращает ID задачи для отслеживания статуса.
    """
    # Создаем задачу в БД
    task = await create_task(
        db=db,
        analyzer_name=task_data.analyzer_name,
        repository_url=str(task_data.repository_url),
        command_template=task_data.command_template,
    )

    # Асинхронно запускаем анализ
    background_tasks.add_task(
        start_analysis,
        task.task_id,
        task_data.analyzer_name,
        str(task_data.repository_url),
        task_data.command_template,
        db,
    )

    return task


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """Проверяет статус задачи по её ID."""
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Если метрики уже были скачаны, меняем статус
    if task.status == "completed" and task.metrics_downloaded:
        return {"task_id": task.task_id, "status": "data_already_retrieved"}

    return {"task_id": task.task_id, "status": task.status}


@router.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Отменяет выполнение задачи анализа."""
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Проверяем, что задачу можно отменить
    if task.status not in ["pending", "running"]:
        return CancelTaskResponse(
            task_id=task_id,
            status=task.status,
            message=f"Task cannot be cancelled because it is in '{task.status}' state",
        )

    # Обновляем статус в БД
    await update_task_status(db, task_id, "cancelling")

    # Отправляем запрос на отмену в Runner сервис
    success = await cancel_analysis(task_id)

    if success:
        # Обновляем статус в БД на "cancelled"
        await update_task_status(db, task_id, "cancelled")
        return CancelTaskResponse(
            task_id=task_id,
            status="cancelled",
            message="Task has been successfully cancelled",
        )
    else:
        # Возвращаем статус в "running", если не удалось отменить
        await update_task_status(db, task_id, task.status)
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel task. It might be already completed or failed.",
        )


@router.get("/tasks/{task_id}/metrics")
async def download_metrics(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Скачивает файл с метриками для анализа.
    После успешной загрузки, запрашивает очистку ресурсов у runner сервиса.
    """
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")

    if task.metrics_downloaded:
        raise HTTPException(status_code=404, detail="Metrics already downloaded")

    try:
        # Получаем файл метрик от runner сервиса
        metrics_data, content_type = await get_metrics_file(task_id)

        # Отмечаем, что метрики скачаны
        await mark_metrics_downloaded(db, task_id)

        # Возвращаем файл как ответ
        return Response(
            content=metrics_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=metrics_comparison_{task_id}.csv"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
