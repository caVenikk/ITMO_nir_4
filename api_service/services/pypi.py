from typing import Any, Dict, List

import httpx

from config import get_settings

settings = get_settings()


async def search_pypi_packages(query: str = "") -> List[Dict[str, Any]]:
    """
    Ищет пакеты в PyPI Simple API с фильтрацией по статическим анализаторам.

    Возвращает список пакетов, отсортированных по релевантности для статического анализа.
    """
    url = "https://pypi.org/simple/"
    headers = {"Accept": "application/vnd.pypi.simple.v1+json"}

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    # Получаем все пакеты
    packages = data.get("projects", [])

    # Если есть запрос, применяем релевантную сортировку
    if query:
        query = query.lower()

        # Создаем три категории по релевантности
        exact_matches = []  # Точное совпадение
        prefix_matches = []  # Начинаются с запроса
        substring_matches = []  # Содержат запрос где-то внутри

        for pkg in packages:
            name = pkg.get("name", "").lower()

            if name == query:
                exact_matches.append(pkg)
            elif name.startswith(query):
                prefix_matches.append(pkg)
            elif query in name:
                substring_matches.append(pkg)

        # Сортируем каждую категорию по _last-serial (популярности)
        exact_matches = sorted(
            exact_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )
        prefix_matches = sorted(
            prefix_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )
        substring_matches = sorted(
            substring_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )

        # Объединяем все группы в порядке релевантности
        filtered_packages = exact_matches + prefix_matches + substring_matches
    else:
        # Если запрос не указан, фильтруем по ключевым словам для анализаторов
        analyzer_keywords = [
            "lint",
            "pep8",
            "flake",
            "pylint",
            "pycodestyle",
            "check",
            "static",
            "analyze",
            "mypy",
            "type",
            "bandit",
            "security",
            "ast",
            "ruff",
            "black",
            "isort",
            "pyright",
        ]

        # Разделяем на три группы релевантности
        exact_matches = []  # Точные совпадения с ключевыми словами
        prefix_matches = []  # Начинаются с ключевых слов
        substring_matches = []  # Содержат ключевые слова

        for pkg in packages:
            name = pkg.get("name", "").lower()

            # Проверяем, соответствует ли имя пакета полностью одному из ключевых слов
            if name in analyzer_keywords:
                exact_matches.append(pkg)
                continue

            # Проверяем префикс
            for keyword in analyzer_keywords:
                if name.startswith(keyword) and pkg not in exact_matches:
                    prefix_matches.append(pkg)
                    break

            # Если не префикс, проверяем подстроку
            if pkg not in exact_matches and pkg not in prefix_matches:
                if any(keyword in name for keyword in analyzer_keywords):
                    substring_matches.append(pkg)

        # Сортируем каждую категорию по _last-serial (популярности)
        exact_matches = sorted(
            exact_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )
        prefix_matches = sorted(
            prefix_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )
        substring_matches = sorted(
            substring_matches, key=lambda pkg: pkg.get("_last-serial", 0), reverse=True
        )

        # Объединяем все группы в порядке релевантности
        filtered_packages = exact_matches + prefix_matches + substring_matches

    # Ограничиваем количество результатов
    return filtered_packages[:100]
