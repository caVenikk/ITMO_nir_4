import logging
from typing import Optional

import httpx

from config import get_settings

settings = get_settings()
logger = logging.getLogger("runner.api_client")


class APIClient:
    """Клиент для взаимодействия с API сервисом"""

    def __init__(self):
        self.base_url = settings.api_service_url
        self.timeout = settings.api_request_timeout

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None,
        metrics_file: Optional[str] = None,
    ) -> bool:
        """
        Отправляет обновление статуса задачи в API сервис.

        Args:
            task_id: ID задачи
            status: Новый статус задачи
            error: Сообщение об ошибке (если есть)
            metrics_file: Путь к файлу с метриками (если есть)

        Returns:
            bool: Успешность обновления
        """
        url = f"{self.base_url}/internal/tasks/{task_id}/status"

        payload = {"status": status, "error": error, "metrics_file": metrics_file}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending status update to {url}: {payload}")
                response = await client.post(url, json=payload)

                if response.status_code != 200:
                    logger.error(
                        f"Ошибка при обновлении статуса задачи {task_id}: {response.text}"
                    )
                    return False

                return True
        except Exception as e:
            logger.error(
                f"Исключение при обновлении статуса задачи {task_id}: {str(e)}"
            )
            return False


# Глобальный экземпляр клиента
api_client = APIClient()
