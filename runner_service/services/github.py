import asyncio
import logging
import os
import shutil
from typing import Optional, Tuple

import git

from config import get_settings

settings = get_settings()
logger = logging.getLogger("runner.github")


async def clone_repository(
    repository_url: str, task_id: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Клонирует репозиторий по URL в директорию для задачи.

    Args:
        repository_url: URL репозитория GitHub
        task_id: ID задачи

    Returns:
        Tuple[bool, Optional[str], Optional[str]]:
            - Успешность операции
            - Путь к клонированному репозиторию (если успешно)
            - Сообщение об ошибке (если неуспешно)
    """
    # Создаем директорию для репозитория
    repo_dir = os.path.join(settings.repos_dir, task_id)
    os.makedirs(repo_dir, exist_ok=True)

    logger.info(f"Клонирование репозитория {repository_url} в {repo_dir}")

    try:
        # Запускаем клонирование асинхронно через выполнение в отдельном потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: git.Repo.clone_from(repository_url, repo_dir, depth=1)
        )

        logger.info(f"Репозиторий {repository_url} успешно клонирован в {repo_dir}")
        return True, repo_dir, None

    except Exception as e:
        logger.error(f"Ошибка при клонировании репозитория {repository_url}: {str(e)}")
        # Очищаем директорию, если что-то пошло не так
        shutil.rmtree(repo_dir, ignore_errors=True)
        return False, None, str(e)


async def remove_repository(task_id: str) -> bool:
    """
    Удаляет директорию с клонированным репозиторием.

    Args:
        task_id: ID задачи

    Returns:
        bool: Успешность операции
    """
    repo_dir = os.path.join(settings.repos_dir, task_id)

    if not os.path.exists(repo_dir):
        logger.warning(f"Директория репозитория {repo_dir} не существует")
        return True

    try:
        # Удаляем директорию
        shutil.rmtree(repo_dir, ignore_errors=True)
        logger.info(f"Директория репозитория {repo_dir} успешно удалена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении директории репозитория {repo_dir}: {str(e)}")
        return False
