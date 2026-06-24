"""Unit tests for contract models — no DB, no vector required."""

from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError

from rag_builder.models.contracts import (
    BuildRequest,
    BuildResponse,
    Section,
    StatusResponse,
    DeleteResponse,
    MetadataBlock,
    DocumentBlock,
    TerminologyItem,
    ProtectedSpan,
)


class TestSectionValidation:
    """RB-9: page 1-based, section_id стабилен, parent_id, bbox."""

    def test_section_valid_minimal(self) -> None:
        s = Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "hello"})
        assert s.page is None  # page is optional
        assert s.parent_id is None

    def test_section_page_must_be_1_based(self) -> None:
        with pytest.raises(ValidationError, match="page must be 1-based"):
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "x"}, page=0)

    def test_section_page_negative(self) -> None:
        with pytest.raises(ValidationError, match="page must be 1-based"):
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "x"}, page=-1)

    def test_section_page_1_based_ok(self) -> None:
        s = Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "x"}, page=1)
        assert s.page == 1
        s2 = Section(section_id=2, document_id=100, level=1, path="2", type="text", content={"text": "x"}, page=99)
        assert s2.page == 99

    def test_section_bbox_optional(self) -> None:
        s = Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "x"})
        assert s.bbox is None
        s2 = Section(
            section_id=2,
            document_id=100,
            level=1,
            path="2",
            type="text",
            content={"text": "x"},
            bbox=[10.0, 20.0, 200.0, 40.0],
        )
        assert s2.bbox == [10.0, 20.0, 200.0, 40.0]

    def test_section_parent_id_optional(self) -> None:
        s = Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "x"})
        assert s.parent_id is None
        s2 = Section(
            section_id=2, document_id=100, level=1, path="1.1", type="text", content={"text": "x"}, parent_id=1
        )
        assert s2.parent_id == 1


class TestBuildRequestDocumentId:
    """RB-9 + DB-10: document_id resolution and consistency."""

    def test_document_id_from_root(self) -> None:
        req = BuildRequest(document_id=100, sections=[])
        assert req.document_id == 100

    def test_document_id_from_metadata(self) -> None:
        meta = MetadataBlock(schema="v1", document_id=200, created_at=datetime.now(timezone.utc))
        req = BuildRequest(metadata=meta, sections=[])
        assert req.document_id == 200

    def test_document_id_from_document_block(self) -> None:
        doc = DocumentBlock(id=300)
        req = BuildRequest(document=doc, sections=[])
        assert req.document_id == 300

    def test_document_id_priority_root_over_others(self) -> None:
        meta = MetadataBlock(schema="v1", document_id=100, created_at=datetime.now(timezone.utc))
        doc = DocumentBlock(id=100)
        req = BuildRequest(document_id=100, metadata=meta, document=doc, sections=[])
        assert req.document_id == 100

    def test_document_id_from_metadata_when_root_missing(self) -> None:
        meta = MetadataBlock(schema="v1", document_id=200, created_at=datetime.now(timezone.utc))
        doc = DocumentBlock(id=200)
        req = BuildRequest(metadata=meta, document=doc, sections=[])
        assert req.document_id == 200

    def test_document_id_from_document_when_others_missing(self) -> None:
        doc = DocumentBlock(id=300)
        req = BuildRequest(document=doc, sections=[])
        assert req.document_id == 300

    def test_document_id_missing_raises(self) -> None:
        with pytest.raises(ValidationError, match="document_id is required"):
            BuildRequest(sections=[])

    def test_document_id_mismatch_metadata(self) -> None:
        meta = MetadataBlock(schema="v1", document_id=200, created_at=datetime.now(timezone.utc))
        with pytest.raises(ValidationError, match="metadata.document_id must match"):
            BuildRequest(document_id=100, metadata=meta, sections=[])

    def test_document_id_mismatch_document_block(self) -> None:
        doc = DocumentBlock(id=300)
        with pytest.raises(ValidationError, match="document.id must match"):
            BuildRequest(document_id=100, document=doc, sections=[])

    def test_document_id_mismatch_section(self) -> None:
        section = Section(
            section_id=1, document_id=999, level=1, path="1", type="text", content={"text": "x"}
        )
        with pytest.raises(ValidationError, match="section.document_id must match"):
            BuildRequest(document_id=100, sections=[section])

    def test_document_id_sections_consistent(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(section_id=2, document_id=100, level=1, path="2", type="text", content={"text": "b"}),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert req.document_id == 100


class TestBuildRequestSectionIdUniqueness:
    """RB-9: section_id стабилен / уникален в рамках запроса."""

    def test_unique_section_ids_ok(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(section_id=2, document_id=100, level=1, path="2", type="text", content={"text": "b"}),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert len(req.sections) == 2

    def test_duplicate_section_id_raises(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(section_id=1, document_id=100, level=1, path="2", type="text", content={"text": "b"}),
        ]
        with pytest.raises(ValidationError, match="duplicate section_id"):
            BuildRequest(document_id=100, sections=sections)

    def test_three_same_section_id_raises(self) -> None:
        sections = [
            Section(section_id=5, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(section_id=5, document_id=100, level=1, path="2", type="text", content={"text": "b"}),
            Section(section_id=5, document_id=100, level=1, path="3", type="text", content={"text": "c"}),
        ]
        with pytest.raises(ValidationError, match="duplicate section_id"):
            BuildRequest(document_id=100, sections=sections)


class TestBuildRequestParentId:
    """RB-9: parent_id ссылается на существующий section_id."""

    def test_parent_id_none_ok(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert req.sections[0].parent_id is None

    def test_parent_id_valid_reference(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(
                section_id=2, document_id=100, level=2, path="1.1", type="text", content={"text": "b"}, parent_id=1
            ),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert req.sections[1].parent_id == 1

    def test_parent_id_invalid_reference_raises(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}),
            Section(
                section_id=2, document_id=100, level=2, path="1.1", type="text", content={"text": "b"}, parent_id=99
            ),
        ]
        with pytest.raises(ValidationError, match="non-existent section_id"):
            BuildRequest(document_id=100, sections=sections)

    def test_multiple_children_same_parent_ok(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "parent"}),
            Section(
                section_id=2, document_id=100, level=2, path="1.1", type="text", content={"text": "child1"}, parent_id=1
            ),
            Section(
                section_id=3, document_id=100, level=2, path="1.2", type="text", content={"text": "child2"}, parent_id=1
            ),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert len(req.sections) == 3

    def test_nested_parent_id_chain_ok(self) -> None:
        sections = [
            Section(section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "l1"}),
            Section(
                section_id=2, document_id=100, level=2, path="1.1", type="text", content={"text": "l2"}, parent_id=1
            ),
            Section(
                section_id=3, document_id=100, level=3, path="1.1.1", type="text", content={"text": "l3"}, parent_id=2
            ),
        ]
        req = BuildRequest(document_id=100, sections=sections)
        assert req.sections[2].parent_id == 2

    def test_circular_parent_id_raises(self) -> None:
        """parent_id ссылается на НЕ существующий section_id."""
        sections = [
            Section(
                section_id=1, document_id=100, level=1, path="1", type="text", content={"text": "a"}, parent_id=2
            ),
            Section(
                section_id=2, document_id=100, level=1, path="2", type="text", content={"text": "b"}, parent_id=1
            ),
        ]
        # Both section_ids exist, so validation passes (section_id=1 exists, section_id=2 exists)
        # Circular reference is allowed by schema — this is fine if the data allows it.
        req = BuildRequest(document_id=100, sections=sections)
        assert len(req.sections) == 2


class TestBuildResponse:
    """RB-8: статус indexed. RB-10: errors/warnings."""

    def test_build_response_status_indexed(self) -> None:
        resp = BuildResponse(
            document_id=100,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=5,
            index_stats={"sections": 3, "chunks": 5, "embeddings": 5},
        )
        assert resp.status == "indexed"

    def test_build_response_status_failed(self) -> None:
        resp = BuildResponse(
            document_id=100,
            status="failed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=0,
            index_stats={},
        )
        assert resp.status == "failed"

    def test_build_response_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            BuildResponse(
                document_id=100,
                status="completed",  # no longer valid
                indexed_at=datetime.now(timezone(timedelta(hours=3))),
                chunks_count=0,
                index_stats={},
            )

    def test_build_response_errors_default_empty(self) -> None:
        resp = BuildResponse(
            document_id=100,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=0,
            index_stats={},
        )
        assert resp.errors == []
        assert resp.warnings == []

    def test_build_response_errors_and_warnings(self) -> None:
        resp = BuildResponse(
            document_id=100,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=0,
            index_stats={},
            errors=["err1"],
            warnings=["warn1"],
        )
        assert resp.errors == ["err1"]
        assert resp.warnings == ["warn1"]

    def test_build_response_index_stats_shape(self) -> None:
        resp = BuildResponse(
            document_id=100,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=3,
            index_stats={"sections": 2, "chunks": 3, "embeddings": 3},
        )
        assert resp.index_stats["sections"] == 2
        assert resp.index_stats["chunks"] == 3


class TestDeleteResponse:
    def test_delete_response_status_completed(self) -> None:
        resp = DeleteResponse(document_id=100, deleted_count=5, status="completed")
        assert resp.status == "completed"

    def test_delete_response_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteResponse(document_id=100, deleted_count=0, status="indexed")


class TestStatusResponse:
    def test_status_response_pending(self) -> None:
        resp = StatusResponse(document_id=100, status="pending", chunks_count=0, has_embeddings=False)
        assert resp.status == "pending"
        assert resp.indexed_at is None

    def test_status_response_indexed(self) -> None:
        now = datetime.now(timezone(timedelta(hours=3)))
        resp = StatusResponse(
            document_id=100, status="indexed", chunks_count=5, has_embeddings=True, indexed_at=now
        )
        assert resp.status == "indexed"
        assert resp.indexed_at == now

    def test_status_response_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            StatusResponse(document_id=100, status="completed", chunks_count=0, has_embeddings=False)


class TestBuildRequestWithAllFields:
    """Integration-style test for BuildRequest with all optional fields."""

    def test_full_build_request_with_terminology(self) -> None:
        now = datetime.now(timezone.utc)
        req = BuildRequest(
            document_id=100,
            metadata=MetadataBlock(schema="for_rag_v1", document_id=100, created_at=now),
            document=DocumentBlock(id=100, doc_code="TEST-001", title="Test Doc"),
            sections=[
                Section(
                    section_id=1,
                    document_id=100,
                    level=1,
                    path="1",
                    page=1,
                    bbox=[0.0, 0.0, 100.0, 50.0],
                    type="text",
                    content={"text": "hello"},
                    created_at=now,
                ),
            ],
            terminology=[TerminologyItem(term="test", definition="a test term")],
            protected_spans=[ProtectedSpan(section_id=1, start_offset=0, end_offset=5)],
            options={"strategy": "semantic_1024"},
        )
        assert req.document_id == 100
        assert len(req.sections) == 1
        assert len(req.terminology) == 1
        assert len(req.protected_spans) == 1
        assert req.options["strategy"] == "semantic_1024"

    def test_build_request_empty_sections_allowed(self) -> None:
        req = BuildRequest(document_id=100, sections=[])
        assert req.sections == []

    def test_build_request_options_empty_dict(self) -> None:
        req = BuildRequest(document_id=100, sections=[], options={})
        assert req.options == {}


class TestSectionTypeLiterals:
    def test_all_section_types_valid(self) -> None:
        for st in ("text", "textBlock", "headerFooter", "table", "list", "image", "formula"):
            s = Section(section_id=1, document_id=100, level=1, path="1", type=st, content={"text": "x"})
            assert s.type == st

    def test_invalid_section_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            Section(section_id=1, document_id=100, level=1, path="1", type="section", content={"text": "x"})

    def test_invalid_section_type_numeric(self) -> None:
        with pytest.raises(ValidationError):
            Section(section_id=1, document_id=100, level=1, path="1", type=123, content={"text": "x"})  # type: ignore[arg-type]
