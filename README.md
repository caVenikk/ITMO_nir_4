# Система анализа метрик производительности

Данный проект предоставляет систему для сбора, анализа и визуализации метрик производительности различных инструментов (систем статического анализа Python-кода). Он состоит из трех основных компонентов: Фронтенд-сервис, API-сервис и Сервис запуска.

## Структура проекта

```
nir4/
├── api_service/     # Бэкенд-сервис для хранения данных и API-эндпоинтов
├── runner_service/  # Сервис для запуска инструментов и сбора метрик
└── frontend/        # Веб-интерфейс для визуализации и анализа
```

## Компоненты

### Фронтенд

Фронтенд-сервис предоставляет пользовательский интерфейс для загрузки, анализа и визуализации данных о метриках производительности статических анализаторов кода Python-приложений. Он включает функциональность для:

-   Парсинга CSV-данных, содержащих метрики производительности
-   Агрегации метрик по инструментам
-   Расчета статистики (мин, макс, среднее) для метрик
-   Визуализации сравнения производительности между инструментами

### API-сервис

API-сервис обрабатывает хранение данных и предоставляет эндпоинты для получения и манипуляции данными. Он использует:

-   FastAPI для реализации REST API
-   SQLAlchemy для операций с базой данных
-   aiosqlite для асинхронного доступа к базе данных

### Сервис запуска

Сервис запуска отвечает за:

-   Выполнение инструментов и измерение их производительности
-   Сбор метрик, таких как время выполнения, использование CPU и потребление памяти
-   Отправку метрик обратно в API-сервис

Он использует:

-   GitPython для работы с репозиториями
-   FastAPI для предоставления эндпоинтов
-   aiofiles для асинхронных операций с файлами

## Ключевые метрики

Система отслеживает следующие метрики производительности:

-   **Время выполнения** (секунды)
-   **Использование ЦП** (процент)
-   **Использование памяти** (КБ)
