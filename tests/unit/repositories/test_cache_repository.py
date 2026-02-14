"""CacheRepositoryのユニットテスト."""

from datetime import datetime, timezone
from unittest.mock import Mock

from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.repositories.cache_repository import CacheRepository


def _create_repository() -> tuple[CacheRepository, Mock]:
    dynamodb_resource = Mock()
    table = Mock()
    dynamodb_resource.Table.return_value = table
    repository = CacheRepository(dynamodb_resource=dynamodb_resource, table_name="cache-table")
    return repository, table


def test_put_stores_tags_field() -> None:
    repository, table = _create_repository()

    judgment = JudgmentResult(
        url="https://example.com/a",
        title="Title",
        description="Description",
        interest_label=InterestLabel.ACT_NOW,
        buzz_label=BuzzLabel.HIGH,
        confidence=0.95,
        summary="Reason",
        model_id="model",
        judged_at=datetime(2026, 2, 14, 0, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc),
        tags=["Kotlin", "Claude"],
    )

    repository.put(judgment)

    put_item = table.put_item.call_args.kwargs["Item"]
    assert put_item["tags"] == ["Kotlin", "Claude"]


def test_get_restores_tags_when_present() -> None:
    repository, table = _create_repository()
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#abc",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/a",
            "title": "Title",
            "description": "Description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "Reason",
            "model_id": "model",
            "judged_at": "2026-02-14T00:00:00+00:00",
            "published_at": "2026-02-13T12:00:00+00:00",
            "tags": ["Kotlin", "Claude"],
        }
    }

    result = repository.get("https://example.com/a")

    assert result is not None
    assert result.tags == ["Kotlin", "Claude"]


def test_get_uses_empty_tags_when_missing() -> None:
    repository, table = _create_repository()
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#abc",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/a",
            "title": "Title",
            "description": "Description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "Reason",
            "model_id": "model",
            "judged_at": "2026-02-14T00:00:00+00:00",
            "published_at": "2026-02-13T12:00:00+00:00",
        }
    }

    result = repository.get("https://example.com/a")

    assert result is not None
    assert result.tags == []


def test_cache_repository_get_with_summary() -> None:
    """新規キャッシュ（summaryフィールド）の読み込みを検証."""
    repository, table = _create_repository()
    # 新規のキャッシュデータ（summaryフィールドを持つ）
    table.get_item.return_value = {
        "Item": {
            "PK": "URL#def",
            "SK": "JUDGMENT#v1",
            "url": "https://example.com/new-cache",
            "title": "New Cache Title",
            "description": "New cache description",
            "interest_label": "ACT_NOW",
            "buzz_label": "HIGH",
            "confidence": 0.95,
            "summary": "This is a new cache summary",
            "model_id": "model-new",
            "judged_at": "2026-02-15T00:00:00+00:00",
            "published_at": "2026-02-14T12:00:00+00:00",
            "tags": ["Kotlin", "AWS"],
        }
    }

    result = repository.get("https://example.com/new-cache")

    assert result is not None
    assert result.summary == "This is a new cache summary"
    assert result.url == "https://example.com/new-cache"


def test_cache_repository_put_with_summary() -> None:
    """summaryフィールドが正しく保存されることを検証."""
    repository, table = _create_repository()

    judgment = JudgmentResult(
        url="https://example.com/save-test",
        title="Save Test Title",
        description="Save test description",
        interest_label=InterestLabel.FYI,
        buzz_label=BuzzLabel.LOW,
        confidence=0.75,
        summary="This is a test summary for saving",
        model_id="test-model",
        judged_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        published_at=datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc),
        tags=["Test", "Cache"],
    )

    repository.put(judgment)

    put_item = table.put_item.call_args.kwargs["Item"]
    assert put_item["summary"] == "This is a test summary for saving"
    assert "reason" not in put_item  # reasonフィールドは保存されない
