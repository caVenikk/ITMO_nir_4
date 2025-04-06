from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# PyPI пакеты
class PyPIPackage(BaseModel):
    name: str
    last_serial: Optional[int] = Field(None, validation_alias="_last-serial")


class PyPISearchResponse(BaseModel):
    packages: List[PyPIPackage]


# Задачи анализа
class TaskCreate(BaseModel):
    analyzer_name: str
    repository_url: HttpUrl
    command_template: str = "{analyzer_cmd} {path}"  # Шаблон команды для запуска


class TaskResponse(BaseModel):
    task_id: str
    analyzer_name: str
    repository_url: str
    command_template: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str

    class Config:
        from_attributes = True


# Внутренний API
class TaskStatusUpdate(BaseModel):
    """Модель для обновления статуса задачи от Runner сервиса"""

    status: str
    error: Optional[str] = None
    metrics_file: Optional[str] = None


# Отмена задачи
class CancelTaskResponse(BaseModel):
    """Модель ответа на запрос отмены задачи"""

    task_id: str
    status: str
    message: str
