import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, Field, field_validator

from app.models.task import TaskStatus


class TaskCreateRequest(BaseModel):
    source_urls: list[HttpUrl] = Field(min_length=1)

    @field_validator("source_urls")
    @classmethod
    def validate_non_empty_urls(cls, value: list[HttpUrl]) -> list[HttpUrl]:
        if not value:
            raise ValueError("source_urls must not be empty")
        return value


class TaskCreateResponse(BaseModel):
    task_id: uuid.UUID


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: uuid.UUID
    status: TaskStatus
    urls_processed: int
    metrics_generated: int | None
    created_at: datetime
    updated_at: datetime
    error: str | None = None
