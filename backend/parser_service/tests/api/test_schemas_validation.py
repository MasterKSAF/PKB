"""
Тесты Pydantic-схем: валидация запросов для v1 и v2.
"""
import pytest
from pydantic import ValidationError
from app.api.v1.schemas import PreviewRequest, ProcessRequest as V1ProcessRequest
from app.api.v2.schemas import ProcessRequest as V2ProcessRequest, ProcessingMode


class TestV1Schemas:
    def test_preview_request_valid(self):
        req = PreviewRequest(task_id=1, version_id="v1", file_key="test.pdf", max_pages=5)
        assert req.max_pages == 5

    def test_preview_request_invalid_max_pages(self):
        with pytest.raises(ValidationError):
            PreviewRequest(task_id=1, version_id="v1", file_key="test.pdf", max_pages=0)
        with pytest.raises(ValidationError):
            PreviewRequest(task_id=1, version_id="v1", file_key="test.pdf", max_pages=101)

    def test_preview_request_forbidden_options(self):
        with pytest.raises(ValidationError, match="extract_tables cannot be True"):
            PreviewRequest(task_id=1, version_id="v1", file_key="t.pdf",
                           options={"extract_tables": True})
        with pytest.raises(ValidationError, match="extract_images cannot be True"):
            PreviewRequest(task_id=1, version_id="v1", file_key="t.pdf",
                           options={"extract_images": True})

    def test_process_request_empty_version_id(self):
        with pytest.raises(ValidationError):
            V1ProcessRequest(task_id=1, version_id="", file_key="f.pdf")


class TestV2Schemas:
    def test_preview_mode_requires_max_pages(self):
        with pytest.raises(ValidationError, match="max_pages is required for preview mode"):
            V2ProcessRequest(task_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW)

    def test_preview_mode_forbidden_options(self):
        with pytest.raises(ValidationError, match="extract_tables cannot be True"):
            V2ProcessRequest(task_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW,
                             max_pages=3, options={"extract_tables": True})
        with pytest.raises(ValidationError, match="extract_images cannot be True"):
            V2ProcessRequest(task_id=1, file_key="f.pdf", mode=ProcessingMode.PREVIEW,
                             max_pages=3, options={"extract_images": True})

    def test_full_mode_allows_any_options(self):
        req = V2ProcessRequest(task_id=1, file_key="f.pdf", mode=ProcessingMode.FULL,
                               options={"extract_tables": True, "extract_images": True})
        assert req.options["extract_tables"] is True