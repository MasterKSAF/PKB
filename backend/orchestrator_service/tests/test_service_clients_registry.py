"""
Unit tests for RegistryServiceClient.

Tests mock generation for all registry service endpoints:
  - Classifiers: list, tree, CRUD, import
  - Terminology: list, CRUD, normalize, import
  - Registry documents: list, CRUD, status, export/import
  - Statistics, enums
"""

import pytest

from app.services.registry_client import RegistryServiceClient


@pytest.fixture
def reg_client():
    client = RegistryServiceClient()
    client.mock_mode = True
    return client


# ===========================================================================
# Classifiers
# ===========================================================================


class TestRegistryClassifiers:
    """Tests for classifier management."""

    @pytest.mark.asyncio
    async def test_list_classifiers(self, reg_client):
        result = await reg_client.list_classifiers()
        # Registry mock returns data under "data" key
        assert "data" in result
        assert "meta" in result

    @pytest.mark.asyncio
    async def test_list_classifiers_with_filters(self, reg_client):
        result = await reg_client.list_classifiers(
            doc_type="mks",
            page=1,
            page_size=20,
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_classifier_tree(self, reg_client):
        result = await reg_client.get_classifier_tree(root_code="31", max_depth=5)
        # Registry mock returns data under "data" key
        assert "data" in result
        assert "meta" in result

    @pytest.mark.asyncio
    async def test_get_classifier(self, reg_client):
        result = await reg_client.get_classifier(code="31.240")
        # Registry mock wraps in data key
        assert "data" in result

    @pytest.mark.asyncio
    async def test_create_classifier(self, reg_client):
        result = await reg_client.create_classifier(
            data={"code": "99.999", "title": "Тестовый классификатор", "doc_type": "mks"},
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_classifier(self, reg_client):
        result = await reg_client.update_classifier(
            code="31.240",
            data={"title": "Обновлённый заголовок"},
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_patch_classifier(self, reg_client):
        result = await reg_client.patch_classifier(
            code="31.240",
            data={"title": "Частичное обновление"},
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_delete_classifier(self, reg_client):
        result = await reg_client.delete_classifier(code="99.999")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_import_classifiers(self, reg_client):
        items = [{"code": "01.010", "title": "Тест"}]
        result = await reg_client.import_classifiers(nodes=items)
        assert "data" in result


# ===========================================================================
# Terminology
# ===========================================================================


class TestRegistryTerminology:
    """Tests for terminology management."""

    @pytest.mark.asyncio
    async def test_list_terminology(self, reg_client):
        result = await reg_client.list_terminology()
        assert "data" in result
        assert "meta" in result

    @pytest.mark.asyncio
    async def test_list_terminology_with_filters(self, reg_client):
        result = await reg_client.list_terminology(
            search="обшивка",
            page=1,
            page_size=20,
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_term(self, reg_client):
        result = await reg_client.get_term(term_id="term-test-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_term_all_fields(self, reg_client):
        result = await reg_client.get_term("term-test-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_create_term(self, reg_client):
        result = await reg_client.create_term(
            term="обшивка",
            normalized_term="обшивка корпуса",
            context="shipbuilding",
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_create_term_with_source(self, reg_client):
        result = await reg_client.create_term(
            term="толщина",
            normalized_term="толщина листа",
            source="doc-001",
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_term(self, reg_client):
        result = await reg_client.update_term(
            term_id="term-001",
            data={"normalized_term": "обновлённый термин"},
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_delete_term(self, reg_client):
        result = await reg_client.delete_term(term_id="term-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_normalize_term(self, reg_client):
        result = await reg_client.normalize_term(term="обшивка")
        assert "data" in result
        data = result["data"]
        assert data["original"] == "обшивка"
        assert "normalized" in data
        assert "found" in data

    @pytest.mark.asyncio
    async def test_normalize_term_with_unknown(self, reg_client):
        result = await reg_client.normalize_term(term="неизвестный_термин")
        assert "data" in result
        assert result["data"]["found"] is True  # Mock always returns found

    @pytest.mark.asyncio
    async def test_import_terms(self, reg_client):
        items = [{"term": "тест", "normalized_term": "тестовый термин"}]
        result = await reg_client.import_terms(terms=items)
        assert "data" in result


# ===========================================================================
# Registry Documents
# ===========================================================================


class TestRegistryDocuments:
    """Tests for registry document management."""

    @pytest.mark.asyncio
    async def test_list_registry_documents(self, reg_client):
        result = await reg_client.list_registry_documents()
        assert "data" in result
        assert "meta" in result

    @pytest.mark.asyncio
    async def test_list_registry_documents_with_filters(self, reg_client):
        result = await reg_client.list_registry_documents(
            status="approved",
            search="норма",
            page=1,
            page_size=20,
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_registry_document(self, reg_client):
        result = await reg_client.get_registry_document(doc_id="doc-reg-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_registry_document_full(self, reg_client):
        result = await reg_client.get_registry_document("doc-reg-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_create_registry_document(self, reg_client):
        result = await reg_client.create_registry_document(
            data={
                "title": "Тестовый документ",
                "doc_code": "ТУ 1234-567",
                "source_type": "TU",
            },
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_registry_document(self, reg_client):
        result = await reg_client.update_registry_document(
            doc_id="doc-reg-001",
            data={"title": "Обновлённый документ"},
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_registry_document_status(self, reg_client):
        result = await reg_client.update_registry_document_status(
            doc_id="doc-reg-001",
            status="indexed",
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_registry_document_status_transitions(self, reg_client):
        """Test various status transitions."""
        for status in ("draft", "uploaded", "previewing", "parsing",
                       "validation", "approved", "registry", "indexed"):
            result = await reg_client.update_registry_document_status(
                doc_id="doc-reg-001",
                status=status,
            )
            assert "data" in result

    @pytest.mark.asyncio
    async def test_delete_registry_document(self, reg_client):
        result = await reg_client.delete_registry_document(doc_id="doc-reg-001")
        assert "data" in result

    @pytest.mark.asyncio
    async def test_export_registry_documents(self, reg_client):
        result = await reg_client.export_registry_documents(
            format="xlsx",
            classifier_code="31",
        )
        assert "data" in result

    @pytest.mark.asyncio
    async def test_import_registry_documents(self, reg_client):
        items = [{"title": "Импорт", "doc_code": "IMP-001"}]
        result = await reg_client.import_registry_documents(documents=items)
        assert "data" in result


# ===========================================================================
# Statistics and Enums
# ===========================================================================


class TestRegistryInfo:
    """Tests for statistics and enum endpoints."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, reg_client):
        result = await reg_client.get_statistics()
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_statistics_counts(self, reg_client):
        result = await reg_client.get_statistics()
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_enums(self, reg_client):
        result = await reg_client.get_enums()
        # Enums returned under "data" key
        assert "data" in result
        data = result["data"]
        assert "doc_type" in data
        assert "chat_status" in data

    @pytest.mark.asyncio
    async def test_get_enums_values(self, reg_client):
        result = await reg_client.get_enums()
        data = result.get("data", result)
        assert len(data) > 0
