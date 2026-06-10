"""
Тесты для result_builder.py
"""
from datetime import datetime
from app.services.result_builder import ResultBuilder
from app.config import settings


def test_result_builder_full():
    final_json = {
        "content": {
            "document": {"source": {"file_name": "test.pdf"}},
            "quality": {"confidence": 0.95},
            "errors": [],
            "status": "completed"
        }
    }
    result = ResultBuilder.build(task_id=123, final_json=final_json, mode="full")
    assert result["task_id"] == 123
    assert result["metadata"]["mode"] == "full"
    assert result["metadata"]["preview_not_supported"] is False
    assert result["metadata"]["schema"] == settings.parsing_schema
    assert result["document"] == {"source": {"file_name": "test.pdf"}}
    assert result["quality"] == {"confidence": 0.95}
    assert result["errors"] == []
    assert result["status"] == "completed"


def test_result_builder_preview_with_flag():
    final_json = {
        "content": {
            "document": {},
            "quality": {},
            "errors": [],
            "status": "preview"
        }
    }
    result = ResultBuilder.build(
        task_id=456, final_json=final_json, mode="preview", preview_not_supported=True
    )
    assert result["metadata"]["mode"] == "preview"
    assert result["metadata"]["preview_not_supported"] is True
    assert result["status"] == "preview"
    assert "created_at" in result["metadata"]


def test_result_builder_missing_fields():
    final_json = {}  # нет content
    result = ResultBuilder.build(task_id=1, final_json=final_json, mode="full")
    assert result["document"] == {}
    assert result["quality"] == {}
    assert result["errors"] == []
    assert result["status"] == "completed"