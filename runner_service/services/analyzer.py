import asyncio
import logging
import os
from typing import Any, Dict, Optional

from config import get_settings
from services.api_client import api_client
from services.github import clone_repository, remove_repository
from services.package import install_package, uninstall_package

settings = get_settings()
logger = logging.getLogger("runner.analyzer")


async def start_analysis_task(
    task_id: str,
    analyzer_name: str,
    repository_url: str,
    command_template: str,
    iterations: int,
    active_tasks: Dict[str, Dict[str, Any]],
) -> None:
    """
    Выполняет анализ кода в репозитории с помощью стандартных анализаторов и пользовательского, если указан.

    Args:
        task_id: ID задачи
        analyzer_name: Имя пакета анализатора
        repository_url: URL репозитория
        command_template: Шаблон команды для запуска анализатора
        iterations: Количество итераций для метрик
        active_tasks: Словарь активных задач для отслеживания процессов
    """
    try:
        # Определяем, является ли анализатор стандартным
        standard_analyzers = ["ruff", "black", "flake8"]
        is_standard_analyzer = analyzer_name in standard_analyzers

        # Шаг 1: Установка анализатора, если он не является стандартным
        if not is_standard_analyzer:
            logger.info(f"Установка пользовательского анализатора {analyzer_name}")
            success, error = await install_package(analyzer_name)
            if not success:
                await api_client.update_task_status(
                    task_id=task_id,
                    status="failed",
                    error=f"Failed to install analyzer: {error}",
                )
                # Удаляем задачу из активных
                if task_id in active_tasks:
                    del active_tasks[task_id]
                return

        # Шаг 2: Клонирование репозитория
        logger.info(f"Клонирование репозитория {repository_url}")
        success, repo_dir, error = await clone_repository(repository_url, task_id)
        if not success:
            await api_client.update_task_status(
                task_id=task_id,
                status="failed",
                error=f"Failed to clone repository: {error}",
            )
            # Удаляем задачу из активных
            if task_id in active_tasks:
                del active_tasks[task_id]
            return

        # Шаг 3: Запуск анализаторов и сбор метрик
        logger.info(
            f"Запуск анализаторов на репозитории {repository_url} с {iterations} итерациями"
        )
        logger.info(f"Используемый шаблон команды: {command_template}")
        metrics_file_path = os.path.join(settings.metrics_dir, f"metrics_{task_id}.csv")

        # Определяем параллелизм на основе числа доступных CPU
        parallel_arg = "1"  # По умолчанию 1 для слабых серверов
        if os.cpu_count() is not None and os.cpu_count() > 1:  # type: ignore
            parallel_arg = "2"  # Используем 2 потока, если есть больше 1 CPU

        # Базовая команда для запуска Go-сборщика
        cmd = [
            settings.compiled_collector_path,
            "-target",
            repo_dir or ".",
            "-iterations",
            str(iterations),
            "-output",
            metrics_file_path,
            "-parallel",
            parallel_arg,
            "-smart=true",
            "-command-template",
            command_template,
        ]

        # Добавляем пользовательский анализатор, если он не стандартный
        if not is_standard_analyzer:
            cmd.extend(["-custom-analyzer", analyzer_name])
            logger.info(f"Включен пользовательский анализатор: {analyzer_name}")

        logger.info(f"Запуск команды: {' '.join(cmd)}")

        try:
            # Запускаем сборщик метрик и ожидаем завершения с таймаутом
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            # Сохраняем процесс в словаре активных задач
            if task_id in active_tasks:
                active_tasks[task_id]["process"] = proc

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=settings.analyze_timeout
                )

                # Задача могла быть отменена пока мы ждали
                if (
                    task_id in active_tasks
                    and active_tasks[task_id].get("status") == "cancelled"
                ):
                    logger.info(
                        f"Задача {task_id} была отменена, пропускаем обработку результатов"
                    )
                    return

                stdout_text = stdout.decode("utf-8") if stdout else ""
                stderr_text = stderr.decode("utf-8") if stderr else ""

                logger.info(f"Вывод процесса: {stdout_text}")
                if stderr_text:
                    logger.warning(f"Ошибки процесса: {stderr_text}")

                if proc.returncode != 0 and not stderr_text.strip():
                    # Проверяем только критические ошибки, когда нет вывода в stderr
                    # Ненулевой код возврата от анализаторов - это нормально
                    error_msg = "Unknown error during analysis"
                    raise RuntimeError(f"Ошибка при выполнении анализа: {error_msg}")

                # Проверяем, что файл метрик создан
                if not os.path.exists(metrics_file_path):
                    raise RuntimeError("Файл метрик не был создан")

                # Проверяем количество строк в файле метрик
                with open(metrics_file_path, "r") as f:
                    line_count = sum(1 for _ in f) - 1  # Вычитаем строку заголовка
                    logger.info(f"Создан файл метрик с {line_count} строками данных")

                expected_lines = iterations * 3  # 3 стандартных анализатора
                if line_count < expected_lines:
                    logger.warning(
                        f"Внимание: количество строк метрик ({line_count}) меньше ожидаемого ({expected_lines})"
                    )

                # Обновляем статус задачи
                await api_client.update_task_status(
                    task_id=task_id, status="completed", metrics_file=metrics_file_path
                )
                logger.info(f"Анализ для задачи {task_id} успешно завершен")

            except asyncio.TimeoutError:
                # Обрабатываем превышение таймаута
                await api_client.update_task_status(
                    task_id=task_id,
                    status="failed",
                    error=f"Analysis timed out after {settings.analyze_timeout} seconds",
                )
                logger.error(f"Таймаут при выполнении анализа для задачи {task_id}")
                # Убиваем процесс, если он все еще работает
                try:
                    proc.kill()
                except Exception:
                    pass

        except Exception as e:
            await api_client.update_task_status(
                task_id=task_id,
                status="failed",
                error=f"Error during analysis: {str(e)}",
            )
            logger.error(
                f"Ошибка при выполнении анализа для задачи {task_id}: {str(e)}"
            )

    except Exception as e:
        # Обрабатываем любые исключения
        await api_client.update_task_status(
            task_id=task_id, status="failed", error=f"Unexpected error: {str(e)}"
        )
        logger.error(f"Неожиданная ошибка при выполнении задачи {task_id}: {str(e)}")
    finally:
        # Удаляем задачу из активных
        if task_id in active_tasks:
            del active_tasks[task_id]


async def cancel_task(task_id: str, active_tasks: Dict[str, Dict[str, Any]]) -> bool:
    """
    Отменяет выполнение задачи анализа.

    Args:
        task_id: ID задачи
        active_tasks: Словарь активных задач

    Returns:
        bool: Успешность отмены
    """
    if task_id not in active_tasks:
        logger.warning(f"Попытка отменить несуществующую задачу {task_id}")
        return False

    task_info = active_tasks[task_id]
    proc = task_info.get("process")

    if proc is None:
        logger.warning(f"Процесс для задачи {task_id} не найден")
        return False

    # Отмечаем задачу как отмененную
    task_info["status"] = "cancelled"

    # Останавливаем процесс
    try:
        # Пытаемся сначала аккуратно остановить
        proc.terminate()

        # Ждем до 5 секунд для завершения
        try:
            await asyncio.wait_for(proc.wait(), 5)
        except asyncio.TimeoutError:
            # Если не завершился, убиваем принудительно
            proc.kill()

        # Уведомляем API сервис об отмене
        await api_client.update_task_status(
            task_id=task_id, status="cancelled", error="Task cancelled by user request"
        )

        # Удаляем процесс из словаря
        task_info["process"] = None

        # Запускаем очистку ресурсов
        await cleanup_task(task_id, task_info.get("analyzer_name"))

        logger.info(f"Задача {task_id} успешно отменена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отмене задачи {task_id}: {str(e)}")
        return False


async def cleanup_task(task_id: str, analyzer_name: Optional[str] = None) -> None:
    """
    Удаляет ресурсы, связанные с задачей (пакет, репозиторий, файлы метрик).

    Args:
        task_id: ID задачи
        analyzer_name: Имя пакета анализатора (если известно)
    """
    logger.info(f"Очистка ресурсов для задачи {task_id}")

    try:
        # Удаляем пакет анализатора, если имя предоставлено и это не стандартный анализатор
        if analyzer_name and analyzer_name not in ["ruff", "black", "flake8"]:
            await uninstall_package(analyzer_name)

        # Удаляем репозиторий
        await remove_repository(task_id)

        # Удаляем файл метрик
        metrics_file = os.path.join(settings.metrics_dir, f"metrics_{task_id}.csv")
        if os.path.exists(metrics_file):
            os.remove(metrics_file)
            logger.info(f"Файл метрик {metrics_file} удален")

        # Уведомляем API сервис о завершении очистки
        await api_client.update_task_status(task_id=task_id, status="cleaned")
        logger.info(f"Очистка ресурсов для задачи {task_id} завершена")

    except Exception as e:
        logger.error(f"Ошибка при очистке ресурсов для задачи {task_id}: {str(e)}")
        await api_client.update_task_status(
            task_id=task_id, status="cleanup_failed", error=f"Cleanup failed: {str(e)}"
        )
