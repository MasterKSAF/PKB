"""
Unit tests for ValidationServiceClient.

Tests mock generation for:
  - extract_parameters — извлечение параметров
  - compare — сравнение норм и проекта
  - get_comparison — результат сравнения
  - compare_batch — массовое сравнение
  - check — проверки документа
  - calculate — вычисления
  - recommend — рекомендации
"""

import pytest

from app.services.validate_client import ValidationServiceClient


@pytest.fixture
def validate_client():
    client = ValidationServiceClient()
    client.mock_mode = True
    return client


class TestExtractParameters:
    """Tests for parameter extraction."""

    @pytest.mark.asyncio
    async def test_extract_basic(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-test-001",
            document_type="specification",
        )
        assert "document_id" in result
        assert "document_type" in result
        assert "parameters" in result
        assert "extraction_confidence" in result
        assert result["document_id"] == "doc-test-001"

    @pytest.mark.asyncio
    async def test_extract_parameters_structure(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-001",
            document_type="specification",
        )
        params = result["parameters"]
        assert "designation" in params
        assert "title" in params
        assert "materials" in params
        assert "dimensions" in params

    @pytest.mark.asyncio
    async def test_extract_specification_items(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-001",
            document_type="specification",
        )
        items = result["parameters"]["specification_items"]
        assert len(items) > 0
        item = items[0]
        for field in ("position", "name", "quantity", "dimensions", "weight", "material"):
            assert field in item, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_extract_with_page_id(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-001",
            document_type="specification",
            page_id="page-5",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_confidence_range(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-001",
            document_type="specification",
        )
        assert 0.0 <= result["extraction_confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_extract_unconfirmed_fields(self, validate_client):
        result = await validate_client.extract_parameters(
            document_id="doc-001",
            document_type="specification",
        )
        assert "unconfirmed_fields" in result


class TestCompare:
    """Tests for comparison endpoints."""

    @pytest.mark.asyncio
    async def test_compare_basic(self, validate_client):
        result = await validate_client.compare(
            normative_text="Толщина ≥ 12 мм",
            project_text="Толщина = 14 мм",
            document_type="normative",
        )
        assert "comparison_id" in result
        assert "match_status" in result
        assert "details" in result
        assert "disclaimer" in result
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_compare_match_status(self, validate_client):
        result = await validate_client.compare(
            normative_text="Требование",
            project_text="Проектное решение",
            document_type="normative",
        )
        assert result["match_status"] in ("match", "possible_discrepancy",
                                           "not_found_in_project", "not_found_in_norm",
                                           "insufficient_data")

    @pytest.mark.asyncio
    async def test_compare_disclaimer(self, validate_client):
        result = await validate_client.compare(
            normative_text="Тест",
            project_text="Тест",
            document_type="normative",
        )
        assert "информационный" in result["disclaimer"].lower() or \
               "disclaimer" in result["disclaimer"].lower() or \
               len(result["disclaimer"]) > 0

    @pytest.mark.asyncio
    async def test_get_comparison(self, validate_client):
        result = await validate_client.get_comparison(comparison_id="cmp-test-001")
        assert result["comparison_id"] == "cmp-test-001"
        assert "normative_block" in result
        assert "project_block" in result
        assert "match_status" in result

    @pytest.mark.asyncio
    async def test_get_comparison_full_structure(self, validate_client):
        result = await validate_client.get_comparison("cmp-test-001")
        normative = result["normative_block"]
        for field in ("document_id", "document_title", "page_number", "requirement_text"):
            assert field in normative, f"Missing field: {field}"
        project = result["project_block"]
        for field in ("document_id", "document_title", "page_number", "parameter_text"):
            assert field in project, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_compare_batch_basic(self, validate_client):
        pairs = [
            {"normative": "Толщина ≥ 12 мм", "project": "Толщина = 14 мм"},
            {"normative": "Длина ≥ 5 м", "project": "Длина = 4.5 м"},
        ]
        result = await validate_client.compare_batch(pairs=pairs)
        assert "batch_id" in result
        assert "comparisons" in result
        assert "total_pairs" in result
        assert "matched" in result
        assert result["total_pairs"] == 2

    @pytest.mark.asyncio
    async def test_compare_batch_empty(self, validate_client):
        result = await validate_client.compare_batch(pairs=[])
        assert result["total_pairs"] == 0

    @pytest.mark.asyncio
    async def test_compare_batch_item_structure(self, validate_client):
        pairs = [{"normative": "N1", "project": "P1"}]
        result = await validate_client.compare_batch(pairs=pairs)
        item = result["comparisons"][0]
        for field in ("comparison_id", "match_status", "summary"):
            assert field in item, f"Missing field: {field}"


class TestCheck:
    """Tests for document validation checks."""

    @pytest.mark.asyncio
    async def test_check_document(self, validate_client):
        result = await validate_client.check(
            document_id="doc-001",
            document_type="specification",
        )
        assert "passed" in result
        assert "checks" in result
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_check_result_type(self, validate_client):
        result = await validate_client.check(
            document_id="doc-001",
            document_type="specification",
        )
        assert isinstance(result["passed"], bool)


class TestCalculate:
    """Tests for calculation endpoint."""

    @pytest.mark.asyncio
    async def test_calculate_basic(self, validate_client):
        result = await validate_client.calculate(expression="12 * 50 + 10")
        assert "expression" in result
        assert "result" in result
        assert "unit" in result
        assert "steps" in result

    @pytest.mark.asyncio
    async def test_calculate_with_context(self, validate_client):
        result = await validate_client.calculate(
            expression="thickness * 2",
            context={"thickness": 6},
        )
        assert "result" in result
        assert "unit" in result

    @pytest.mark.asyncio
    async def test_calculate_steps_list(self, validate_client):
        result = await validate_client.calculate(expression="1+1")
        assert isinstance(result["steps"], list)


class TestRecommend:
    """Tests for recommendation endpoint."""

    @pytest.mark.asyncio
    async def test_recommend_basic(self, validate_client):
        failures = [{"failure_ref": "min_thickness_12mm", "detail": "t=10mm"}]
        result = await validate_client.recommend(
            failures=failures,
            document_type="specification",
        )
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_recommend_structure(self, validate_client):
        failures = [{"failure_ref": "test_ref", "detail": "test"}]
        result = await validate_client.recommend(
            failures=failures,
            document_type="normative",
        )
        rec = result["recommendations"][0]
        for field in ("failure_ref", "recommendation_text", "severity", "reference_document"):
            assert field in rec, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_recommend_severity_values(self, validate_client):
        failures = [{"failure_ref": "test"}]
        result = await validate_client.recommend(failures=failures, document_type="normative")
        rec = result["recommendations"][0]
        assert rec["severity"] in ("critical", "warning", "info")
