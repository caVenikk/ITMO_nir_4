import logging
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse

from api.models import AnalyzeTaskCreate, CancelResponse
from config import get_settings
from services.analyzer import cancel_task, cleanup_task, start_analysis_task
from services.api_client import api_client

# Получение настроек
settings = get_settings()

# Настройка логирования
logger = logging.getLogger("runner.api")

router = APIRouter()

# Хранение активных задач и их процессов
active_tasks = {}


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_task(
    task_data: AnalyzeTaskCreate, background_tasks: BackgroundTasks
):
    """
    Создает новую задачу анализа кода.
    Устанавливает анализатор, клонирует репозиторий и запускает сбор метрик.
    """
    try:
        # Проверяем, не запущена ли уже задача с таким ID
        if task_data.task_id in active_tasks:
            return {"status": "already_running", "task_id": task_data.task_id}

        # Сообщаем API-сервису, что задача принята к выполнению
        success = await api_client.update_task_status(
            task_id=task_data.task_id, status="running"
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task status in API service",
            )

        # Создаем запись о задаче в хранилище активных задач
        active_tasks[task_data.task_id] = {
            "status": "running",
            "process": None,  # Процесс будет добавлен позже
            "start_time": datetime.now(),
            "analyzer_name": task_data.analyzer_name,
        }

        # Запускаем задачу в фоне
        background_tasks.add_task(
            start_analysis_task,
            task_id=task_data.task_id,
            analyzer_name=task_data.analyzer_name,
            repository_url=str(task_data.repository_url),
            command_template=task_data.command_template,
            iterations=task_data.iterations,
            active_tasks=active_tasks,
        )

        return {"status": "accepted", "task_id": task_data.task_id}
    except Exception as e:
        logger.error(f"Error in create_analysis_task: {str(e)}")
        if task_data.task_id in active_tasks:
            del active_tasks[task_data.task_id]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process task: {str(e)}",
        )


@router.get("/tasks/{task_id}/metrics")
async def get_metrics(task_id: str):
    """
    Возвращает файл с метриками для заданной задачи.
    """
    # Пытаемся найти файл с метриками
    metrics_file = os.path.join(settings.metrics_dir, f"metrics_{task_id}.csv")

    if not os.path.exists(metrics_file):
        raise HTTPException(status_code=404, detail="Metrics file not found")

    # Возвращаем файл
    return FileResponse(
        path=metrics_file, filename=f"metrics_{task_id}.csv", media_type="text/csv"
    )


@router.post("/tasks/{task_id}/cleanup")
async def request_cleanup(task_id: str, background_tasks: BackgroundTasks):
    """
    Очищает ресурсы для задачи (удаляет пакет, репозиторий и файлы метрик).
    """
    # Получаем информацию о задаче
    task_info = active_tasks.get(task_id)
    analyzer_name: str | None = None

    if task_info:
        analyzer_name = task_info.get("analyzer_name")  # type: ignore
        # Удаляем задачу из активных
        del active_tasks[task_id]

    # Запускаем очистку ресурсов в фоновом режиме
    background_tasks.add_task(cleanup_task, task_id, analyzer_name)

    return {"status": "cleanup_initiated", "task_id": task_id}


@router.post("/tasks/{task_id}/cancel", response_model=CancelResponse)
async def cancel_analysis_task(task_id: str):
    """
    Отменяет выполнение задачи анализа.
    """
    # Проверяем, существует ли задача
    if task_id not in active_tasks:
        return CancelResponse(
            task_id=task_id,
            status="not_found",
            message="Task not found or already completed",
        )

    # Получаем информацию о задаче
    task_info = active_tasks[task_id]

    # Проверяем, запущен ли процесс
    if task_info.get("process") is None:
        return CancelResponse(
            task_id=task_id, status="not_running", message="Task process is not running"
        )

    # Отменяем процесс
    try:
        await cancel_task(task_id, active_tasks)
        return CancelResponse(
            task_id=task_id,
            status="cancelled",
            message="Task has been successfully cancelled",
        )
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return CancelResponse(
            task_id=task_id, status="error", message=f"Failed to cancel task: {str(e)}"
        )
