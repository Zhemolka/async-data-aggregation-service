import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AggregationTask, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, source_urls: list[str]) -> AggregationTask:
        task = AggregationTask(
            source_urls=source_urls,
            status=TaskStatus.pending,
            urls_total=len(source_urls),
            urls_processed=0,
        )
        self._session.add(task)
        await self._session.flush()
        return task

    async def get(self, task_id: uuid.UUID) -> AggregationTask | None:
        return await self._session.get(AggregationTask, task_id)

    async def completed_analytics(self) -> tuple[int, int, int]:
        statement = select(
            func.count(AggregationTask.id),
            func.coalesce(func.sum(AggregationTask.urls_processed), 0),
            func.coalesce(func.sum(AggregationTask.metrics_generated), 0),
        ).where(AggregationTask.status == TaskStatus.completed)
        row = (await self._session.execute(statement)).one()
        return int(row[0]), int(row[1]), int(row[2])
