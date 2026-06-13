"""
Tests for pipeline schemas and FSM enums.

Covers:
  - FSM enum validation (DocumentStatus, StepStatusEnum, PipelineStatusEnum, etc.)
  - Pipeline structure shapes (Processing, ReviewRequired, ReadyForPromotion)
  - Indexation pipeline states
  - Formation → Indexation transition
"""

from datetime import datetime, UTC, timedelta

import pytest

from app.schemas.documents import (
    ChunkSummary,
    ClassificationConfidence,
    ConverterValidatorStep,
    DecisionStep,
    DocumentStatus,
    DocumentStatusProcessing,
    DocumentStatusReadyForPromotion,
    DocumentStatusReviewRequired,
    Era,
    FormationPipeline,
    IndexationPipeline,
    Jurisdiction,
    OcrParserStep,
    ParsingStep,
    PipelineStatusEnum,
    PipelinesField,
    PreviewPhase,
    RagIndexingStep,
    RegistryStep,
    ReprocessMode,
    SourceType,
    StatusPipelines,
    StepStatusEnum,
    ValidityStatus,
    ValidationErrorItem,
    ValidationStep,
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
    """Validate the structure of status responses for all 3 variants."""

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

        # Validation step
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
                                ValidationErrorItem(
                                    code="MISSING_FIELD",
                                    section_id=420012,
                                )
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
        """After Pipeline 1 completes, Pipeline 2 starts."""
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
#  4. VALIDATION ERROR ITEM
# ============================================================================


class TestValidationErrorItem:
    """Tests for ValidationErrorItem schema."""

    def test_validation_error_item_minimal(self):
        """ValidationErrorItem with just code."""
        item = ValidationErrorItem(code="MISSING_FIELD")
        d = item.model_dump()
        assert d["code"] == "MISSING_FIELD"
        assert d["section_id"] is None

    def test_validation_error_item_full(self):
        """ValidationErrorItem with all fields."""
        item = ValidationErrorItem(code="INVALID_VALUE", section_id=420012)
        d = item.model_dump()
        assert d["code"] == "INVALID_VALUE"
        assert d["section_id"] == 420012
