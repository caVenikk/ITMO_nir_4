from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


# Модель для создания задачи анализа
class AnalyzeTaskCreate(BaseModel):
    task_id: str
    analyzer_name: str
    repository_url: HttpUrl
    command_template: str = "{analyzer_cmd} {path}"
    iterations: int = 100


# Модель для ответа о статусе задачи
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    error: Optional[str] = None
    metrics_file: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Модель для запроса очистки ресурсов
class CleanupRequest(BaseModel):
    task_id: str


# Модель для ответа на запрос отмены задачи
class CancelResponse(BaseModel):
    task_id: str
    status: str
    message: str
