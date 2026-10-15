import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.analytics import AnalyticsResponse
from app.api.schemas.task import TaskResponse
from app.models.task import AggregationTask
from app.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = TaskRepository(session)

    async def create_task(self, source_urls: list[str]) -> AggregationTask:
        task = await self._repository.create(source_urls)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def save_celery_task_id(self, task: AggregationTask, celery_task_id: str) -> None:
        task.celery_task_id = celery_task_id
        await self._session.commit()

    async def get_task(self, task_id: uuid.UUID) -> TaskResponse:
        task = await self._repository.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return TaskResponse(
            task_id=task.id,
            status=task.status,
            urls_processed=task.urls_processed,
            metrics_generated=task.metrics_generated,
            created_at=task.created_at,
            updated_at=task.updated_at,
            error=task.error_message,
        )

    async def analytics(self) -> AnalyticsResponse:
        successful, urls, metrics = await self._repository.completed_analytics()
        return AnalyticsResponse(
            total_successful_tasks=successful,
            total_urls_processed=urls,
            total_metrics_generated=metrics,
        )
