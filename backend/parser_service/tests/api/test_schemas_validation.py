"""
Тесты Pydantic-схем: валидация запросов для v1.
"""
import pytest
from pydantic import ValidationError
from app.api.v1.schemas import ProcessRequest as V1ProcessRequest, ProcessingMode


class TestV1Schemas:
    def test_preview_mode_requires_max_pages(self):
        with pytest.raises(ValidationError, match="max_pages is required for preview mode"):
            V1ProcessRequest(task_id=1, draft_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW)

    def test_preview_mode_forbidden_options(self):
        with pytest.raises(ValidationError, match="extract_tables cannot be True"):
            V1ProcessRequest(task_id=1, draft_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW,
                             max_pages=3, options={"extract_tables": True})
        with pytest.raises(ValidationError, match="extract_images cannot be True"):
            V1ProcessRequest(task_id=1, draft_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW,
                             max_pages=3, options={"extract_images": True})

    def test_full_mode_allows_any_options(self):
        req = V1ProcessRequest(task_id=1, draft_id=1, file_key="f.pdf", mode=ProcessingMode.FULL,
                               options={"extract_tables": True, "extract_images": True})
        assert req.options["extract_tables"] is True