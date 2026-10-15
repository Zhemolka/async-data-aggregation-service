import pytest
from pydantic import ValidationError

from app.api.schemas.task import TaskCreateRequest


def test_source_urls_cannot_be_empty() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(source_urls=[])


def test_source_urls_must_be_valid_urls() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(source_urls=["not-a-url"])


def test_valid_urls_are_accepted() -> None:
    payload = TaskCreateRequest(source_urls=["https://example.com", "http://example.org/path"])
    assert len(payload.source_urls) == 2
