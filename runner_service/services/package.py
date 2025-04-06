import asyncio
import logging
import sys
from typing import Optional, Tuple

from config import get_settings

settings = get_settings()
logger = logging.getLogger("runner.package")


async def install_package(package_name: str) -> Tuple[bool, Optional[str]]:
    """
    Устанавливает пакет Python через pip.
    Пропускает установку для стандартных анализаторов.

    Args:
        package_name: Имя пакета

    Returns:
        Tuple[bool, Optional[str]]:
            - Успешность операции
            - Сообщение об ошибке (если неуспешно)
    """
    # Пропускаем установку для стандартных анализаторов
    standard_analyzers = ["ruff", "black", "flake8"]
    if package_name in standard_analyzers:
        logger.info(f"Пакет {package_name} уже предустановлен, пропускаем установку")
        return True, None

    logger.info(f"Установка пакета {package_name}")

    try:
        # Запускаем установку асинхронно
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = (
                stderr.decode()
                if stderr
                else "Unknown error during package installation"
            )
            logger.error(f"Ошибка при установке пакета {package_name}: {error_msg}")
            return False, error_msg

        logger.info(f"Пакет {package_name} успешно установлен")
        return True, None

    except Exception as e:
        logger.error(f"Исключение при установке пакета {package_name}: {str(e)}")
        return False, str(e)


async def uninstall_package(package_name: str) -> bool:
    """
    Удаляет пакет Python через pip.

    Args:
        package_name: Имя пакета

    Returns:
        bool: Успешность операции
    """
    logger.info(f"Удаление пакета {package_name}")

    try:
        # Запускаем удаление асинхронно
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-y",
            package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = (
                stderr.decode()
                if stderr
                else "Unknown error during package uninstallation"
            )
            logger.error(f"Ошибка при удалении пакета {package_name}: {error_msg}")
            return False

        logger.info(f"Пакет {package_name} успешно удален")
        return True

    except Exception as e:
        logger.error(f"Исключение при удалении пакета {package_name}: {str(e)}")
        return False
