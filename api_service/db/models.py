import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy"""

    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=str(uuid.uuid4),
        server_default=str(uuid.uuid4),
    )
    analyzer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    repository_url: Mapped[str] = mapped_column(String(255), nullable=False)
    command_template: Mapped[str] = mapped_column(
        String(255), nullable=False, default="{analyzer_cmd} ."
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, running, completed, failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    metrics_file_path: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    metrics_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
