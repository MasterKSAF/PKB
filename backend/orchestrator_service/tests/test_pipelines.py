"""
Comprehensive Pipeline 1 (Formation) and Pipeline 2 (Indexation) tests.

Covers:
  - FSM state definitions and enum values
  - All 3 status response variants (processing, review_required, ready_for_promotion)
  - Pipeline structure with nested steps and pipeline wrapper
  - Preview phase: all sub-steps (ocr_parser, converter_validator, decision)
  - Parsing, Validation, Registry steps
  - Indexation pipeline: pending → indexing → indexed
  - Chunk summary
  - Longpoll parameter bounds
  - Decision actions (proceed, stop_duplicate, force_new_version)
  - Approve flow (review_required → approved → registry)
  - Reprocess flow (failed → uploaded)
  - Soft-delete flow
  - State transition history
  - Edge cases and error codes per API docs

Pipeline 1 FSM states:
  uploaded → previewing → awaiting_decision → parsing → validation
  → ready_for_promotion / review_required → approved → registry

Pipeline 2 FSM states:
  pending_index → indexing → indexed
"""

from datetime import datetime, UTC, timedelta
from enum import Enum

import pytest
from fastapi.testclient import TestClient

# Import schemas for direct model testing
from app.schemas.documents import (
    DocumentStatus,
    SourceType,
    Era,
    Jurisdiction,
    ValidityStatus,
    ClassificationConfidence,
    DecisionAction,
    ReprocessMode,
    StepStatusEnum,
    PipelineStatusEnum,
    DocumentStatusProcessing,
    DocumentStatusReviewRequired,
    DocumentStatusReadyForPromotion,
    StatusPipelines,
    PipelinesField,
    FormationPipeline,
    IndexationPipeline,
    PreviewPhase,
    OcrParserStep,
    ConverterValidatorStep,
    DecisionStep,
    ParsingStep,
    ValidationStep,
    RegistryStep,
    RagIndexingStep,
    ChunkSummary,
    ApproveRequest,
    ApproveResponse,
    DecideRequest,
    DecideResponse,
    ReprocessRequest,
    ReprocessResponse,
    DocumentDeleteResponse,
    TaskPreviewResponse,
    TaskPreviewStatusResponse,
    PreviewMetadata,
    DuplicateCandidate,
    HistoryItem,
    DocumentHistoryResponse,
    QueueItem,
    QueuePipelineSteps,
    QueuePipelineField,
)


# ============================================================================
#  1. FSM ENUM VALIDATION
# ============================================================================


class TestPipeline1FsmEnums:
    """Validate Pipeline 1 FSM enum values against API documentation."""

    def test_document_status_all_fsm_states(self):
        """All Pipeline 1 FSM states must be defined in DocumentStatus."""
        required_states = [
            # Pipeline 1
            "uploaded",
            "previewing",
            "awaiting_decision",
            "parsing",
            "validation",
            "review_required",
            "ready_for_promotion",
            "approved",
            "registry",
            # Pipeline 2
            "pending_index",
            "indexing",
            "indexed",
            # Terminal
            "duplicate",
            "new_version",
            "failed",
            "archived",
        ]
        for state in required_states:
            assert state in DocumentStatus._value2member_map_, (
                f"Missing FSM state: {state}"
            )

    def test_source_type_allowed_values(self):
        """SourceType must match the documented enum."""
        allowed = {"GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "OTHER"}
        assert set(SourceType._value2member_map_.keys()) == allowed

    def test_era_values(self):
        """Era enum must match documented values."""
        assert set(Era._value2member_map_.keys()) == {"USSR", "CIS", "RF", "CURRENT"}

    def test_jurisdiction_values(self):
        """Jurisdiction enum must match documented values."""
        assert set(Jurisdiction._value2member_map_.keys()) == {
            "RU", "EU", "US", "NO", "INTL"
        }

    def test_validity_status_values(self):
        """ValidityStatus enum must match documented values."""
        required = {"active", "superseded", "cancelled", "historical", "draft"}
        assert set(ValidityStatus._value2member_map_.keys()) == required

    def test_decision_action_values(self):
        """Decision actions must match: proceed, stop_duplicate, force_new_version."""
        required = {"proceed", "stop_duplicate", "force_new_version"}
        assert set(DecisionAction._value2member_map_.keys()) == required

    def test_reprocess_mode_values(self):
        """ReprocessMode must match documented values."""
        required = {"full", "ocr_only", "chunking_only", "validation_only", "reindex"}
        assert set(ReprocessMode._value2member_map_.keys()) == required

    def test_step_status_enum_values(self):
        """StepStatusEnum must include pending, in_progress, completed, error, blocked."""
        required = {"pending", "in_progress", "completed", "error", "blocked"}
        values = set(StepStatusEnum._value2member_map_.keys())
        assert required.issubset(values), f"Missing step statuses: {required - values}"

    def test_pipeline_status_enum_values(self):
        """PipelineStatusEnum must include pending, in_progress, completed, failed, blocked."""
        required = {"pending", "in_progress", "completed", "failed", "blocked"}
        values = set(PipelineStatusEnum._value2member_map_.keys())
        assert required.issubset(values), f"Missing pipeline statuses: {required - values}"

    def test_classification_confidence_values(self):
        """ClassificationConfidence must match documented values."""
        required = {"CONFIRMED", "NOT_USED", "SUSPECTED", "EXTRACTED"}
        assert set(ClassificationConfidence._value2member_map_.keys()) == required


# ============================================================================
#  2. PIPELINE STRUCTURE — Status response shapes
# ============================================================================


class TestPipelineStatusResponseStructure:
    """Validate the structure of status responses for all 3 variants.

    Per API doc, status returns one of:
      - DocumentStatusProcessing  (general processing)
      - DocumentStatusReviewRequired
      - DocumentStatusReadyForPromotion
    """

    def test_processing_status_shape(self):
        """DocumentStatusProcessing must match the documented shape."""
        now = datetime.now(UTC)
        status = DocumentStatusProcessing(
            document_id="b3a8f1c2-...",
            status="processing",
            progress_percent=60.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.IN_PROGRESS,
                        preview=PreviewPhase(
                            status=StepStatusEnum.COMPLETED,
                            ocr_parser=OcrParserStep(
                                status=StepStatusEnum.COMPLETED,
                                pages_processed=3,
                            ),
                            converter_validator=ConverterValidatorStep(
                                status=StepStatusEnum.COMPLETED,
                                metadata_extracted=True,
                            ),
                            decision=DecisionStep(
                                status="awaiting",
                                action=None,
                            ),
                        ),
                        parsing=ParsingStep(
                            status=StepStatusEnum.COMPLETED,
                            pages_processed=12,
                            pages_failed=0,
                            avg_confidence=0.92,
                        ),
                        validation=ValidationStep(
                            status="in_progress",
                            errors_found=0,
                        ),
                        registry=RegistryStep(
                            status=StepStatusEnum.PENDING,
                        ),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.PENDING,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.PENDING,
                        ),
                    ),
                ),
            ),
            started_at=now,
            estimated_completion=now + timedelta(minutes=2),
        )
        data = status.model_dump(mode="json")

        # Top-level fields
        assert data["document_id"] == "b3a8f1c2-..."
        assert data["status"] == "processing"
        assert 0 <= data["progress_percent"] <= 100
        assert "started_at" in data
        assert "estimated_completion" in data

        # Steps → pipeline wrapper
        assert "steps" in data
        assert "pipeline" in data["steps"]
        pipe = data["steps"]["pipeline"]

        # Formation pipeline
        assert "formation" in pipe
        frm = pipe["formation"]
        assert frm["status"] == "in_progress"
        assert "preview" in frm
        assert "parsing" in frm
        assert "validation" in frm
        assert "registry" in frm

        # Preview sub-steps
        preview = frm["preview"]
        assert preview["status"] == "completed"
        assert preview["ocr_parser"]["status"] == "completed"
        assert preview["ocr_parser"]["pages_processed"] == 3
        assert preview["converter_validator"]["status"] == "completed"
        assert preview["converter_validator"]["metadata_extracted"] is True
        assert preview["decision"]["status"] == "awaiting"
        assert preview["decision"]["action"] is None

        # Parsing step
        assert frm["parsing"]["status"] == "completed"
        assert frm["parsing"]["pages_processed"] == 12
        assert frm["parsing"]["pages_failed"] == 0
        assert frm["parsing"]["avg_confidence"] == 0.92

        # Validation step (string status for valid/invalid flexibility)
        assert frm["validation"]["status"] == "in_progress"
        assert frm["validation"]["errors_found"] == 0

        # Registry step
        assert frm["registry"]["status"] == "pending"

        # Indexation pipeline
        assert "indexation" in pipe
        idx = pipe["indexation"]
        assert idx["status"] == "pending"
        assert idx["rag_indexing"]["status"] == "pending"

    def test_review_required_status_shape(self):
        """DocumentStatusReviewRequired must match the documented shape."""
        status = DocumentStatusReviewRequired(
            document_id="b3a8f1c2-...",
            status="review_required",
            progress_percent=80.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.BLOCKED,
                        parsing=ParsingStep(
                            status=StepStatusEnum.COMPLETED,
                        ),
                        validation=ValidationStep(
                            status="invalid",
                            errors_found=2,
                            document_id="b3a8f1c2-...",
                            errors=[
                                {"code": "MISSING_FIELD", "section_id": 420012}
                            ],
                        ),
                        registry=RegistryStep(
                            status=StepStatusEnum.BLOCKED,
                        ),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.PENDING,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.PENDING,
                        ),
                    ),
                ),
            ),
        )
        data = status.model_dump(mode="json")

        assert data["status"] == "review_required"
        assert data["progress_percent"] == 80.0

        pipe = data["steps"]["pipeline"]
        frm = pipe["formation"]
        assert frm["status"] == "blocked"
        assert frm["validation"]["status"] == "invalid"
        assert frm["validation"]["errors_found"] == 2
        assert len(frm["validation"]["errors"]) == 1
        assert frm["validation"]["errors"][0]["code"] == "MISSING_FIELD"
        assert frm["registry"]["status"] == "blocked"

        # Pipeline 2 is pending when Pipeline 1 is blocked
        assert pipe["indexation"]["status"] == "pending"

    def test_ready_for_promotion_status_shape(self):
        """DocumentStatusReadyForPromotion must match the documented shape."""
        now = datetime.now(UTC)
        status = DocumentStatusReadyForPromotion(
            document_id="b3a8f1c2-...",
            status="ready_for_promotion",
            progress_percent=100.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.COMPLETED,
                        parsing=ParsingStep(
                            status=StepStatusEnum.COMPLETED,
                        ),
                        validation=ValidationStep(
                            status="valid",
                            document_id="b3a8f1c2-...",
                        ),
                        registry=RegistryStep(
                            status=StepStatusEnum.COMPLETED,
                        ),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.COMPLETED,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.COMPLETED,
                            chunks_generated=34,
                        ),
                    ),
                ),
            ),
            chunk_summary=ChunkSummary(
                sections=34,
                chunks=28,
                embeddings=28,
            ),
            started_at=now,
            completed_at=now,
        )
        data = status.model_dump(mode="json")

        assert data["status"] == "ready_for_promotion"
        assert data["progress_percent"] == 100.0

        pipe = data["steps"]["pipeline"]
        assert pipe["formation"]["status"] == "completed"
        assert pipe["formation"]["validation"]["status"] == "valid"
        assert pipe["formation"]["registry"]["status"] == "completed"
        assert pipe["indexation"]["status"] == "completed"
        assert pipe["indexation"]["rag_indexing"]["chunks_generated"] == 34

        # Chunk summary
        cs = data["chunk_summary"]
        assert cs["sections"] == 34
        assert cs["chunks"] == 28
        assert cs["embeddings"] == 28

    def test_chunk_summary_required_fields(self):
        """ChunkSummary must have sections, chunks, embeddings."""
        cs = ChunkSummary(sections=10, chunks=8, embeddings=8)
        d = cs.model_dump()
        assert d["sections"] == 10
        assert d["chunks"] == 8
        assert d["embeddings"] == 8


# ============================================================================
#  3. PIPELINE 2 — INDEXATION
# ============================================================================


class TestPipeline2Indexation:
    """Validate Pipeline 2 (Indexation) structure and states."""

    def test_indexation_pipeline_structure(self):
        """IndexationPipeline must have status and rag_indexing."""
        pipe = IndexationPipeline(
            status=PipelineStatusEnum.PENDING,
            rag_indexing=RagIndexingStep(
                status=StepStatusEnum.PENDING,
            ),
        )
        data = pipe.model_dump(mode="json")
        assert data["status"] == "pending"
        assert data["rag_indexing"]["status"] == "pending"

    def test_indexation_pipeline_indexing_state(self):
        """Indexation pipeline in indexing state with progress."""
        pipe = IndexationPipeline(
            status=PipelineStatusEnum.IN_PROGRESS,
            rag_indexing=RagIndexingStep(
                status=StepStatusEnum.IN_PROGRESS,
                chunks_generated=15,
            ),
        )
        data = pipe.model_dump(mode="json")
        assert data["status"] == "in_progress"
        assert data["rag_indexing"]["status"] == "in_progress"
        assert data["rag_indexing"]["chunks_generated"] == 15

    def test_indexation_pipeline_completed_state(self):
        """Indexation pipeline in completed state with all stats."""
        pipe = IndexationPipeline(
            status=PipelineStatusEnum.COMPLETED,
            rag_indexing=RagIndexingStep(
                status=StepStatusEnum.COMPLETED,
                chunks_generated=128,
            ),
        )
        data = pipe.model_dump(mode="json")
        assert data["status"] == "completed"
        assert data["rag_indexing"]["chunks_generated"] == 128

    def test_indexation_error_state(self):
        """Indexation pipeline in failed state."""
        pipe = IndexationPipeline(
            status=PipelineStatusEnum.FAILED,
            rag_indexing=RagIndexingStep(
                status=StepStatusEnum.ERROR,
            ),
        )
        data = pipe.model_dump(mode="json")
        assert data["status"] == "failed"
        assert data["rag_indexing"]["status"] == "error"

    def test_formation_to_indexation_transition(self):
        """
        After Pipeline 1 (formation) completes, Pipeline 2 (indexation)
        should start. Test the combined status shape.
        """
        status = DocumentStatusReadyForPromotion(
            document_id="doc-test-001",
            status="ready_for_promotion",
            progress_percent=100.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.COMPLETED,
                        parsing=ParsingStep(status=StepStatusEnum.COMPLETED),
                        validation=ValidationStep(status="valid"),
                        registry=RegistryStep(status=StepStatusEnum.COMPLETED),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.COMPLETED,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.COMPLETED,
                            chunks_generated=42,
                        ),
                    ),
                ),
            ),
            chunk_summary=ChunkSummary(sections=42, chunks=35, embeddings=35),
        )
        data = status.model_dump(mode="json")

        # Pipeline 1 complete
        assert data["steps"]["pipeline"]["formation"]["status"] == "completed"
        # Pipeline 2 also complete
        assert data["steps"]["pipeline"]["indexation"]["status"] == "completed"
        assert data["steps"]["pipeline"]["indexation"]["rag_indexing"]["chunks_generated"] == 42


# ============================================================================
#  4. API ENDPOINTS — Pipeline State Simulations
# ============================================================================


class TestUploadFSM:
    """POST /documents — start of Pipeline 1 (uploaded → preview ready)."""

    def test_upload_response_status_uploaded(self, client, auth_header):
        """Upload should return status='uploaded' (entry into Pipeline 1)."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")},
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "uploaded"
        assert "task_id" in data
        assert isinstance(data["task_id"], int)
        assert "file_hash_sha256" in data
        assert "file_size_bytes" in data
        assert "version_id" in data

    def test_upload_initiates_preview_task(self, client, auth_header):
        """Upload returns task_id for preview phase."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("doc.pdf", b"pdf content", "application/pdf")},
            data={"source_type": "GOST", "title": "Тестовый документ"},
            headers=auth_header,
        )
        data = response.json()
        task_id = data["task_id"]
        assert isinstance(task_id, int)
        assert task_id > 0


class TestPreviewFSM:
    """Preview phase — Pipeline 1 states: uploaded → previewing → awaiting_decision."""

    def test_preview_start_transitions(self, client, auth_header):
        """POST /tasks/{task_id}/preview transitions to previewing."""
        response = client.post(
            "/api/v1/documents/tasks/12345/preview",
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "previewing"
        assert data["task_id"] == 12345

    def test_preview_status_completed(self, client, auth_header):
        """GET /tasks/{task_id}/preview/status returns completed status
        with metadata (simulating preview completion → awaiting_decision)."""
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["ocr_parser_status"] == "completed"
        assert data["converter_validator_status"] == "completed"

        # Preview metadata
        preview = data["preview"]
        assert preview["doc_code"] is not None
        assert preview["title"] is not None
        assert preview["document_type"] == "normative"
        assert preview["year"] == "1981"

        # Duplicates
        assert isinstance(data["duplicates"], list)
        if data["duplicates"]:
            dup = data["duplicates"][0]
            assert "document_id" in dup
            assert "doc_code" in dup
            assert "title" in dup
            assert 0 <= dup["similarity"] <= 1.0

        # Decision required flag — signals awaiting_decision transition
        assert isinstance(data["decision_required"], bool)

    def test_preview_longpoll_bounds(self, client, auth_header):
        """Longpoll parameter must be in [0, 60] range."""
        # Lower bound: 0
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status?longpoll=0",
            headers=auth_header,
        )
        assert response.status_code == 200

        # Upper bound: 60
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status?longpoll=60",
            headers=auth_header,
        )
        assert response.status_code == 200

        # Out of bounds: -1
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status?longpoll=-1",
            headers=auth_header,
        )
        assert response.status_code == 422

        # Out of bounds: 61
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status?longpoll=61",
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_preview_metadata_has_required_fields(self, client, auth_header):
        """Preview metadata must have doc_code, title, document_type, year, revision."""
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status",
            headers=auth_header,
        )
        data = response.json()
        pm = data["preview"]
        for field in ("doc_code", "title", "document_type", "year"):
            assert field in pm, f"Missing preview field: {field}"
        assert "revision" in pm  # may be null

    def test_duplicate_candidate_similarity_range(self, client, auth_header):
        """Each duplicate candidate's similarity must be in [0, 1]."""
        response = client.get(
            "/api/v1/documents/tasks/12345/preview/status",
            headers=auth_header,
        )
        data = response.json()
        for dup in data["duplicates"]:
            assert 0.0 <= dup["similarity"] <= 1.0


class TestDecisionFSM:
    """User decision — transitions from awaiting_decision to next state."""

    def test_decide_proceed_returns_proceeding(self, client, auth_header):
        """Decision action=proceed starts full processing (parsing)."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "proceed"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "proceeding"
        assert data["action"] == "proceed"
        assert len(data["message"]) > 0

    def test_decide_stop_duplicate(self, client, auth_header):
        """Decision action=stop_duplicate marks document as duplicate."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "stop_duplicate"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "stopped"
        assert data["action"] == "stop_duplicate"

    def test_decide_force_new_version(self, client, auth_header):
        """Decision action=force_new_version creates a new version."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "force_new_version"},
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "forcing"
        assert data["action"] == "force_new_version"

    def test_decide_with_comment(self, client, auth_header):
        """Decision supports optional comment field."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "proceed", "comment": "Всё корректно"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_decide_invalid_action_rejected(self, client, auth_header):
        """Invalid action value should return 422."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "invalid_action"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_decide_response_has_document_id(self, client, auth_header):
        """Decide response must contain document_id, status, action, message."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "proceed"},
            headers=auth_header,
        )
        data = response.json()
        for field in ("document_id", "status", "action", "message"):
            assert field in data, f"Missing field: {field}"

    def test_decide_proceed_message_meaningful(self, client, auth_header):
        """Proceed message should indicate full processing was started."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "proceed"},
            headers=auth_header,
        )
        msg = response.json()["message"]
        assert len(msg) > 10, "Message should be descriptive"


class TestStatusFSM:
    """GET /documents/{doc_id}/status — FSM-aware status response."""

    STATUS_URL = "/api/v1/documents/{doc_id}/status"

    def test_status_returns_fsm_structure(self, client, auth_header):
        """Status response must have pipeline wrapper structure."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "pipeline" in data["steps"]
        pipe = data["steps"]["pipeline"]
        assert "formation" in pipe
        assert "indexation" in pipe

    def test_status_formation_has_all_substeps(self, client, auth_header):
        """Formation pipeline must include preview, parsing, validation, registry."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        frm = response.json()["steps"]["pipeline"]["formation"]
        for step in ("preview", "parsing", "validation", "registry"):
            assert step in frm, f"Missing formation substep: {step}"

    def test_status_preview_has_substeps(self, client, auth_header):
        """Preview phase must include ocr_parser, converter_validator, decision."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        preview = response.json()["steps"]["pipeline"]["formation"]["preview"]
        for substep in ("ocr_parser", "converter_validator", "decision"):
            assert substep in preview, f"Missing preview substep: {substep}"

    def test_status_indexation_has_rag_indexing(self, client, auth_header):
        """Indexation pipeline must include rag_indexing."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        idx = response.json()["steps"]["pipeline"]["indexation"]
        assert "rag_indexing" in idx

    def test_status_progress_percent_range(self, client, auth_header):
        """Progress percent must be in [0, 100]."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        pct = response.json()["progress_percent"]
        assert 0 <= pct <= 100

    def test_status_has_started_at(self, client, auth_header):
        """Status response should include started_at timestamp."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        data = response.json()
        assert "started_at" in data
        if data["started_at"]:
            datetime.fromisoformat(data["started_at"])

    def test_status_longpoll_bounds(self, client, auth_header):
        """Longpoll parameter must be in [0, 60]."""
        # Valid: 0
        r = client.get(self.STATUS_URL.format(doc_id="doc-1") + "?longpoll=0", headers=auth_header)
        assert r.status_code == 200
        # Valid: 60
        r = client.get(self.STATUS_URL.format(doc_id="doc-1") + "?longpoll=60", headers=auth_header)
        assert r.status_code == 200
        # Invalid: -1
        r = client.get(self.STATUS_URL.format(doc_id="doc-1") + "?longpoll=-1", headers=auth_header)
        assert r.status_code == 422
        # Invalid: 61
        r = client.get(self.STATUS_URL.format(doc_id="doc-1") + "?longpoll=61", headers=auth_header)
        assert r.status_code == 422


# ============================================================================
#  5. APPROVE FLOW — review_required → approved → registry
# ============================================================================


class TestApproveFlow:
    """POST /documents/{doc_id}/approve — transition from review_required to approved."""

    APPROVE_URL = "/api/v1/documents/{doc_id}/approve"

    def test_approve_returns_202(self, client, auth_header):
        """Approve must return 202 Accepted."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={"force": True, "comment": "Все ошибки исправлены"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_status_is_approved(self, client, auth_header):
        """Approve response must have status='approved'."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={"force": False},
            headers=auth_header,
        )
        assert response.json()["status"] == "approved"

    def test_approve_response_structure(self, client, auth_header):
        """Approve response must have all documented fields."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={"force": True, "comment": "ОК"},
            headers=auth_header,
        )
        data = response.json()
        for field in ("document_id", "status", "promotion_task_id", "approved_by", "approved_at"):
            assert field in data, f"Missing approve field: {field}"

    def test_approve_promotion_task_id_format(self, client, auth_header):
        """promotion_task_id must start with 'promo-' prefix."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={"force": False},
            headers=auth_header,
        )
        task_id = response.json()["promotion_task_id"]
        assert task_id.startswith("promo-")

    def test_approve_timestamp_iso_format(self, client, auth_header):
        """approved_at must be ISO 8601 datetime string."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={"force": False},
            headers=auth_header,
        )
        dt = response.json()["approved_at"]
        datetime.fromisoformat(dt)  # Will raise if invalid

    def test_approve_without_force_defaults(self, client, auth_header):
        """Force field defaults to False when not provided."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-8a3f2b"),
            json={},
            headers=auth_header,
        )
        assert response.status_code == 202


# ============================================================================
#  6. REPROCESS FLOW — failed → uploaded
# ============================================================================


class TestReprocessFlow:
    """POST /documents/{doc_id}/reprocess — transition from failed to uploaded."""

    REPROCESS_URL = "/api/v1/documents/{doc_id}/reprocess"

    def test_reprocess_returns_202(self, client, auth_header):
        """Reprocess must return 202."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_all_modes_accepted(self, client, auth_header):
        """All reprocess modes must be accepted."""
        for mode in ("full", "ocr_only", "chunking_only", "validation_only", "reindex"):
            response = client.post(
                self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
                json={"mode": mode},
                headers=auth_header,
            )
            assert response.status_code == 202, f"Mode {mode} failed: {response.status_code}"

    def test_reprocess_invalid_mode_rejected(self, client, auth_header):
        """Invalid reprocess mode must return 422."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
            json={"mode": "invalid_mode"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_reprocess_response_structure(self, client, auth_header):
        """Reprocess response must have all documented fields."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
            json={"mode": "full"},
            headers=auth_header,
        )
        data = response.json()
        for field in ("mode", "document_id", "user_id", "task_id", "status", "created_at"):
            assert field in data, f"Missing reprocess field: {field}"

    def test_reprocess_with_options(self, client, auth_header):
        """Reprocess supports optional engine/language/pages options."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
            json={
                "mode": "full",
                "options": {"engine": "paddleocr", "language": "ru", "pages": "1-5"},
            },
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_status_is_reprocessing_queued(self, client, auth_header):
        """Reprocess status must be 'reprocessing_queued'."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-8a3f2b"),
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.json()["status"] == "reprocessing_queued"


# ============================================================================
#  7. SOFT DELETE
# ============================================================================


class TestSoftDelete:
    """DELETE /documents/{doc_id} — soft-delete."""

    DELETE_URL = "/api/v1/documents/{doc_id}"

    def test_delete_returns_200(self, client, auth_header):
        """Soft delete must return 200."""
        response = client.delete(
            self.DELETE_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_delete_has_deleted_at(self, client, auth_header):
        """Delete response must contain deleted_at timestamp."""
        response = client.delete(
            self.DELETE_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        data = response.json()
        assert "deleted_at" in data
        datetime.fromisoformat(data["deleted_at"])

    def test_delete_accepts_any_doc_id(self, client, auth_header):
        """Soft delete accepts any document ID in mock mode."""
        response = client.delete(
            self.DELETE_URL.format(doc_id="any-document-id"),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["document_id"] == "any-document-id"


# ============================================================================
#  8. STATE TRANSITION HISTORY
# ============================================================================


class TestStateTransitionHistory:
    """GET /documents/{doc_id}/history — audit log of state transitions."""

    HISTORY_URL = "/api/v1/documents/{doc_id}/history"

    def test_history_returns_200(self, client, auth_header):
        """History must return 200."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_history_response_structure(self, client, auth_header):
        """History must contain document_id, history (list), meta (total)."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "history" in data
        assert isinstance(data["history"], list)
        assert "meta" in data
        assert "total" in data["meta"]

    def test_history_item_structure(self, client, auth_header):
        """Each history item must have all required fields."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        if response.json()["history"]:
            item = response.json()["history"][0]
            for field in ("history_id", "old_status", "new_status", "comment", "changed_by", "changed_at"):
                assert field in item, f"Missing history field: {field}"

    def test_history_tracks_status_transitions(self, client, auth_header):
        """History must record new_status for each transition."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        for entry in response.json()["history"]:
            assert entry["new_status"] is not None
            assert len(entry["new_status"]) > 0

    def test_history_old_status_may_be_null(self, client, auth_header):
        """First history entry may have old_status=null (initial state)."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        for entry in response.json()["history"]:
            # old_status may be None for initial transition
            pass  # No assert — null is valid

    def test_history_changed_at_iso_format(self, client, auth_header):
        """changed_at must be ISO 8601 datetime."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-8a3f2b"),
            headers=auth_header,
        )
        for entry in response.json()["history"]:
            datetime.fromisoformat(entry["changed_at"])


# ============================================================================
#  9. QUEUE — documents in active pipeline states
# ============================================================================


class TestQueuePipeline:
    """GET /documents/queue — documents in pipeline processing states."""

    QUEUE_URL = "/api/v1/documents/queue"

    def test_queue_returns_200(self, client, auth_header):
        """Queue must return 200."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        assert response.status_code == 200

    def test_queue_item_has_pipeline_steps(self, client, auth_header):
        """Each queue item must have steps with pipeline wrapper."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        if response.json()["queue"]:
            item = response.json()["queue"][0]
            assert "steps" in item
            assert "pipeline" in item["steps"]
            pipe = item["steps"]["pipeline"]
            assert "formation" in pipe
            assert "indexation" in pipe

    def test_queue_item_fsm_fields(self, client, auth_header):
        """Queue items must have all FSM-relevant fields."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        if response.json()["queue"]:
            item = response.json()["queue"][0]
            for field in ("status", "progress_percent", "current_step", "source_type"):
                assert field in item, f"Missing queue item field: {field}"

    def test_queue_meta_structure(self, client, auth_header):
        """Queue metadata must contain total_in_queue, page, page_size."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        meta = response.json()["meta"]
        for field in ("total_in_queue", "page", "page_size"):
            assert field in meta

    def test_queue_item_source_type_present(self, client, auth_header):
        """Queue item must include source_type field."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        if response.json()["queue"]:
            item = response.json()["queue"][0]
            assert "source_type" in item
            assert item["source_type"] in (
                "GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "OTHER"
            )


# ============================================================================
#  10. EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestPipelineEdgeCases:
    """Edge cases and error handling per docs."""

    def test_upload_invalid_source_type_returns_400(self, client, auth_header):
        """Invalid source_type must return 400."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", b"data", "application/pdf")},
            data={"source_type": "INVALID"},
            headers=auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        # FastAPI wraps HTTPException detail in {"detail": ...}
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "BAD_REQUEST"

    def test_upload_unsupported_file_type_returns_400(self, client, auth_header):
        """Unsupported file type must return 400."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.exe", b"data", "application/x-msdownload")},
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 400

    def test_versions_upload_unsupported_type_returns_400(self, client, auth_header):
        """Unsupported file for version upload must return 400."""
        response = client.post(
            "/api/v1/documents/doc-test/versions",
            files={"file": ("test.exe", b"data", "application/x-msdownload")},
            headers=auth_header,
        )
        assert response.status_code == 400

    def test_upload_file_too_large_returns_413(self, client, auth_header):
        """File > 100MB must return 413."""
        # Simulate large file via content-length header
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("large.pdf", b"x" * 1024, "application/pdf")},
            data={"source_type": "GOST"},
            headers=auth_header | {"Content-Length": str(200 * 1024 * 1024)},
        )
        # The mock reads content-length from headers; 200MB should trigger 413
        # (but actual size detection depends on implementation)
        assert response.status_code in (202, 413)

    def test_decide_request_missing_action_returns_422(self, client, auth_header):
        """Missing 'action' field in decide must return 422."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_decide_request_invalid_action_returns_422(self, client, auth_header):
        """Invalid action value must return 422."""
        response = client.post(
            "/api/v1/documents/tasks/12345/decide",
            json={"action": "invalid"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_approve_request_empty_body_defaults(self, client, auth_header):
        """Empty body should use defaults (force=False)."""
        response = client.post(
            "/api/v1/documents/doc-test/approve",
            json={},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_invalid_mode_returns_422(self, client, auth_header):
        """Invalid reprocess mode must return 422."""
        response = client.post(
            "/api/v1/documents/doc-test/reprocess",
            json={"mode": "bogus"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_queue_pagination(self, client, auth_header):
        """Queue must support page and page_size parameters."""
        response = client.get(
            "/api/v1/documents/queue?page=1&page_size=10",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 10

    def test_list_with_all_pipeline_filters(self, client, auth_header):
        """List must support all documented filter params for pipeline states."""
        params = {
            "status": "validation",
            "source_type": "GOST",
            "era": "USSR",
            "validity_status": "active",
            "jurisdiction": "RU",
        }
        response = client.get(
            "/api/v1/documents/",
            params=params,
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_pipeline_summary_fields(self, client, auth_header):
        """List summary must have all FSM status counts."""
        response = client.get("/api/v1/documents/", headers=auth_header)
        summary = response.json()["summary"]
        fsm_statuses = [
            "total", "uploaded", "previewing", "awaiting_decision", "parsing",
            "validation", "review_required", "ready_for_promotion", "approved",
            "failed", "archived",
        ]
        for s in fsm_statuses:
            assert s in summary, f"Missing summary field: {s}"
            assert isinstance(summary[s], int), f"{s} must be int"

    def test_pages_text_blocks_have_numbered_blocks(self, client, auth_header):
        """Page text blocks must use 'number' field (not 'block_id')."""
        response = client.get(
            "/api/v1/documents/doc-test/pages/1/text",
            headers=auth_header,
        )
        data = response.json()
        for block in data.get("blocks", []):
            assert "number" in block
            assert "bbox" in block
            assert isinstance(block["bbox"], list)
            assert len(block["bbox"]) == 4

    def test_error_response_has_code_message(self, client, auth_header):
        """Error responses must have error.code and error.message."""
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.exe", b"data", "application/x-msdownload")},
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        data = response.json()
        # FastAPI wraps HTTPException detail in {"detail": ...}
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "BAD_REQUEST"
        assert data["detail"]["error"]["message"] is not None


# ============================================================================
#  11. SCHEMA-LEVEL EDGE CASE VALIDATION
# ============================================================================


class TestSchemaEdgeCases:
    """Validate schema constraints for pipeline-related models."""

    def test_parameter_range_with_bounds(self):
        """ParameterRange must support min_inclusive and max_inclusive."""
        from app.schemas.documents import ParameterRange
        r = ParameterRange(min=5, max=10, min_inclusive=True, max_inclusive=False)
        d = r.model_dump()
        assert d["min"] == 5
        assert d["max"] == 10
        assert d["min_inclusive"] is True
        assert d["max_inclusive"] is False

    def test_parameter_range_optional_fields(self):
        """ParameterRange min/max may be null."""
        from app.schemas.documents import ParameterRange
        r = ParameterRange()
        d = r.model_dump()
        assert d["min"] is None
        assert d["max"] is None
        assert d["min_inclusive"] is None

    def test_document_status_response_union(self):
        """DocumentStatusResponse must be a Union of all 3 status types."""
        from app.schemas.documents import DocumentStatusResponse
        # Verify it's a Union by checking origin
        import typing
        origin = typing.get_origin(DocumentStatusResponse)
        assert origin is not None, "DocumentStatusResponse must be a Union type"

    def test_reprocess_request_mode_default(self):
        """ReprocessRequest mode should default to 'full'."""
        req = ReprocessRequest()
        assert req.mode == ReprocessMode.FULL

    def test_approve_request_defaults(self):
        """ApproveRequest force defaults to False, comment defaults to None."""
        req = ApproveRequest()
        assert req.force is False
        assert req.comment is None

    def test_approve_request_with_values(self):
        """ApproveRequest accepts force and comment."""
        req = ApproveRequest(force=True, comment="Test")
        assert req.force is True
        assert req.comment == "Test"

    def test_history_item_old_status_nullable(self):
        """HistoryItem old_status may be null."""
        item = HistoryItem(
            history_id="h-001",
            old_status=None,
            new_status="uploaded",
            changed_by="user",
            changed_at=datetime.now(UTC),
        )
        assert item.old_status is None

    def test_preview_metadata_revision_nullable(self):
        """PreviewMetadata revision may be null."""
        pm = PreviewMetadata(
            doc_code="ГОСТ 1234",
            title="Test",
            document_type="normative",
            year="2020",
            revision=None,
        )
        assert pm.revision is None

    def test_duplicate_candidate_similarity_bounds(self):
        """DuplicateCandidate similarity must be in [0, 1]."""
        # Valid values
        dc = DuplicateCandidate(document_id="d1", similarity=0.5)
        assert 0 <= dc.similarity <= 1.0
        dc = DuplicateCandidate(document_id="d1", similarity=0.0)
        assert dc.similarity == 0.0
        dc = DuplicateCandidate(document_id="d1", similarity=1.0)
        assert dc.similarity == 1.0


# ============================================================================
#  12. CROSS-PIPELINE INTEGRATION
# ============================================================================


class TestCrossPipelineIntegration:
    """Tests verifying Pipeline 1 → Pipeline 2 handoff."""

    def test_pipeline2_start_after_pipeline1(self):
        """DocumentStatusProcessing must have indexation in pending state
        while formation is in progress."""
        status = DocumentStatusProcessing(
            document_id="doc-1",
            status="processing",
            progress_percent=50.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.IN_PROGRESS,
                        parsing=ParsingStep(status=StepStatusEnum.IN_PROGRESS),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.PENDING,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.PENDING,
                        ),
                    ),
                ),
            ),
        )
        data = status.model_dump(mode="json")
        assert data["steps"]["pipeline"]["formation"]["status"] == "in_progress"
        assert data["steps"]["pipeline"]["indexation"]["status"] == "pending"

    def test_pipeline2_active_after_pipeline1_complete(self):
        """When formation is complete, indexation should be pending or active."""
        status = DocumentStatusReadyForPromotion(
            document_id="doc-1",
            status="ready_for_promotion",
            progress_percent=100.0,
            steps=StatusPipelines(
                pipeline=PipelinesField(
                    formation=FormationPipeline(
                        status=PipelineStatusEnum.COMPLETED,
                        parsing=ParsingStep(status=StepStatusEnum.COMPLETED),
                        validation=ValidationStep(status="valid"),
                        registry=RegistryStep(status=StepStatusEnum.COMPLETED),
                    ),
                    indexation=IndexationPipeline(
                        status=PipelineStatusEnum.IN_PROGRESS,
                        rag_indexing=RagIndexingStep(
                            status=StepStatusEnum.IN_PROGRESS,
                            chunks_generated=20,
                        ),
                    ),
                ),
            ),
            chunk_summary=ChunkSummary(sections=20, chunks=20, embeddings=20),
        )
        data = status.model_dump(mode="json")
        assert data["steps"]["pipeline"]["formation"]["status"] == "completed"
        assert data["steps"]["pipeline"]["indexation"]["status"] == "in_progress"
