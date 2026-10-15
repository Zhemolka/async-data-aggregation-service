# Async Data Aggregation Service

Тестовый backend-сервис для асинхронной агрегации аналитических данных с веб-ресурсов.
Запрос на обработку создаётся через FastAPI, сохраняется в PostgreSQL и передаётся в Celery.
Celery-воркер имитирует долгую сетевую работу, а клиент может независимо запрашивать статус
задачи и агрегированную статистику.

## Стек

- Python 3.10+
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg
- PostgreSQL
- Celery
- Redis как broker и result backend
- Alembic
- Docker + Docker Compose
- pytest + Ruff

## Что реализовано

- `POST /api/v1/tasks` — создание фоновой задачи, мгновенный `202 Accepted`.
- Валидация непустого списка синтаксически корректных URL.
- Статусы `pending -> processing -> completed` и `failed` при ошибке.
- Имитация сетевой задержки по 2 секунды на каждый URL.
- Любой URL, содержащий подстроку `error`, переводит всю задачу в `failed`.
- Для успешной задачи генерируется случайная метрика от 10 до 100.
- `GET /api/v1/tasks/{task_id}` — статус и результат задачи.
- `GET /api/v1/analytics` — агрегаты по всем `completed` задачам.
- Миграции Alembic выполняются автоматически при запуске `app`.
- Конфигурация полностью через переменные окружения.
- Docker Compose поднимает `app`, `worker`, `redis`, `db` одной командой.

## Быстрый запуск

### 1. Подготовить `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 2. Запустить проект

```bash
docker compose up --build
```

После запуска:

- Swagger: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

Контейнеры:

- `app` — FastAPI;
- `worker` — Celery worker;
- `redis` — Celery broker + result backend;
- `db` — PostgreSQL.

## API

### Создание задачи

```http
POST /api/v1/tasks
Content-Type: application/json
```

```json
{
  "source_urls": [
    "https://example.com/page-1",
    "https://example.com/page-2",
    "https://example.com/page-3"
  ]
}
```

Ответ:

```http
HTTP/1.1 202 Accepted
```

```json
{
  "task_id": "5b0568cf-e53a-4c7e-8c82-24a03fbcf35b"
}
```

API не ждёт окончания фоновой обработки. После записи в БД задача отправляется в Celery.

### Получение статуса

```http
GET /api/v1/tasks/5b0568cf-e53a-4c7e-8c82-24a03fbcf35b
```

Пример завершённой задачи:

```json
{
  "task_id": "5b0568cf-e53a-4c7e-8c82-24a03fbcf35b",
  "status": "completed",
  "urls_processed": 3,
  "metrics_generated": 42,
  "created_at": "2026-10-15T10:00:00Z",
  "updated_at": "2026-10-15T10:00:06Z",
  "error": null
}
```

Возможные статусы: `pending`, `processing`, `completed`, `failed`.

### Проверка ошибки

Создайте задачу с URL, содержащим `error`:

```json
{
  "source_urls": [
    "https://example.com/page-1",
    "https://example.com/error"
  ]
}
```

Воркeр прервёт выполнение всей задачи и сохранит текст ошибки. `GET /tasks/{task_id}` вернёт
`status: "failed"` и заполненное поле `error`.

### Агрегированная статистика

```http
GET /api/v1/analytics
```

```json
{
  "total_successful_tasks": 15,
  "total_urls_processed": 45,
  "total_metrics_generated": 630
}
```

В статистику входят только успешно завершённые (`completed`) задачи.

## Структура проекта

```text
app/
├── api/
│   ├── routes/          # HTTP endpoints
│   └── schemas/         # Pydantic request/response schemas
├── core/
│   ├── config.py        # env configuration
│   └── database.py      # async SQLAlchemy engine/session
├── models/              # SQLAlchemy models
├── repositories/        # database queries
├── services/            # application/business logic
└── tasks/               # Celery app and worker logic
alembic/                  # database migrations
tests/                    # unit tests
```

## Миграции

При старте контейнера `app` автоматически выполняется:

```bash
alembic upgrade head
```

Вручную внутри контейнера:

```bash
docker compose exec app alembic upgrade head
```

## Тесты и lint

Локально:

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

или:

```bash
make lint
make test
```

## Design decisions

### Почему API и Celery разделены

HTTP-процесс отвечает только за быстрый приём запросов и чтение состояния. Долгая работа вынесена
в отдельный Celery worker, поэтому `POST /tasks` может вернуть `202 Accepted` сразу и не блокировать
FastAPI worker на время имитации сети.

### Почему PostgreSQL — источник состояния задачи

Статус и результат хранятся в PostgreSQL, а не только в Celery result backend. Это позволяет API
получать состояние задачи независимо от жизненного цикла записей Celery/Redis и удобно строить
аналитические запросы по завершённым задачам.

### Почему SQLAlchemy работает асинхронно

FastAPI использует `asyncpg` и `AsyncSession`, чтобы операции с БД не блокировали event loop. В Celery
синхронная точка входа вызывает отдельную async-функцию через `asyncio.run`, поэтому слой доступа к
данным остаётся единообразным между API и worker.

### Почему URL обрабатываются последовательно

ТЗ допускает последовательную или параллельную обработку. Последовательный вариант выбран намеренно:
он проще, детерминированно демонстрирует задержку `2 сек × количество URL` и делает сценарий остановки
при первом `error` очевидным. При реальной сетевой агрегации этот участок легко заменить на параллельный
`asyncio.gather` с ограничением конкуренции через semaphore.

### Почему Redis используется и как broker, и как result backend

Это прямо соответствует требованию задания и уменьшает количество инфраструктурных компонентов.
При этом бизнес-результат задачи всё равно хранится в PostgreSQL; Redis используется Celery для очереди
и технического состояния выполнения.

## Полезные команды

```bash
# Запуск
docker compose up --build

# Логи API и worker
docker compose logs -f app worker

# Остановка
docker compose down

# Полный сброс вместе с данными PostgreSQL
docker compose down -v
```
