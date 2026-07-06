"""
Unit tests for DraftFSM and TaskStatus/TaskStage enums.
"""

import pytest

from app.core.fsm import DraftFSM, DraftState, TaskStage, TaskStatus


class TestDraftFSM:
    """Tests for DraftFSM stateless validator."""

    def test_valid_transitions(self):
        assert DraftFSM.can_transition(DraftState.UPLOADED, DraftState.PREVIEWING)
        assert DraftFSM.can_transition(DraftState.PREVIEWING, DraftState.READY_FOR_APPROVE)
        assert DraftFSM.can_transition(DraftState.READY_FOR_APPROVE, DraftState.PROCESSING)
        assert DraftFSM.can_transition(DraftState.READY_FOR_APPROVE, DraftState.DISCARDED)
        assert DraftFSM.can_transition(DraftState.PROCESSING, DraftState.APPROVED)
        assert DraftFSM.can_transition(DraftState.PROCESSING, DraftState.DISCARDED)

    def test_invalid_transitions(self):
        assert not DraftFSM.can_transition(DraftState.UPLOADED, DraftState.APPROVED)
        assert not DraftFSM.can_transition(DraftState.UPLOADED, DraftState.DISCARDED)
        assert not DraftFSM.can_transition(DraftState.UPLOADED, DraftState.PROCESSING)
        assert not DraftFSM.can_transition(DraftState.READY_FOR_APPROVE, DraftState.APPROVED)
        assert not DraftFSM.can_transition(DraftState.APPROVED, DraftState.UPLOADED)
        assert not DraftFSM.can_transition(DraftState.DISCARDED, DraftState.READY_FOR_APPROVE)

    def test_validate_transition_success(self):
        DraftFSM.validate_transition(DraftState.UPLOADED, DraftState.PREVIEWING)

    def test_validate_transition_failure(self):
        with pytest.raises(ValueError):
            DraftFSM.validate_transition(DraftState.UPLOADED, DraftState.APPROVED)

    def test_allowed_transitions_from(self):
        allowed = DraftFSM.allowed_transitions_from(DraftState.READY_FOR_APPROVE)
        assert sorted(allowed) == sorted([DraftState.PROCESSING.value, DraftState.DISCARDED.value])

    def test_allowed_transitions_from_unknown(self):
        assert DraftFSM.allowed_transitions_from("unknown") == []

    def test_is_terminal_approved(self):
        assert DraftFSM.is_terminal(DraftState.APPROVED)

    def test_is_terminal_discarded(self):
        assert DraftFSM.is_terminal(DraftState.DISCARDED)

    def test_is_not_terminal_uploaded(self):
        assert not DraftFSM.is_terminal(DraftState.UPLOADED)

    def test_is_not_terminal_previewing(self):
        assert not DraftFSM.is_terminal(DraftState.PREVIEWING)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_values(self):
        assert TaskStatus.ACTIVE.value == "active"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_all_values(self):
        values = [s.value for s in TaskStatus]
        assert sorted(values) == ["active", "completed", "failed", "partially_indexed", "queued"]

    def test_partially_indexed(self):
        """partially_indexed is a valid status (P2I-1)."""
        assert TaskStatus.PARTIALLY_INDEXED.value == "partially_indexed"


class TestTaskStage:
    """Tests for TaskStage enum."""

    def test_values(self):
        assert TaskStage.UPLOAD.value == "upload"
        assert TaskStage.PREVIEW.value == "preview"
        assert TaskStage.DECISION.value == "decision"
        assert TaskStage.FULL.value == "full"
        assert TaskStage.REGISTRY.value == "registry"
        assert TaskStage.INDEXATION.value == "indexation"

    def test_all_values(self):
        values = [s.value for s in TaskStage]
        assert sorted(values) == ["decision", "full", "indexation", "preview", "registry", "upload"]
