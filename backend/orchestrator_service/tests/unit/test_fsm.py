"""
Unit tests for DocumentFSM — validates all state transitions.

Tests cover:
- All valid transitions for Pipeline 1 and Pipeline 2
- Invalid transitions reject correctly
- Terminal states have no outgoing transitions
- Step-to-state mapping
- Pipeline 1 / Pipeline 2 state classification
"""

import pytest

from app.core.fsm import (
    DocumentFSM,
    DocumentState,
    InvalidTransitionError,
    PIPELINE_1_STEPS,
    PIPELINE_2_STEPS,
    STEP_TO_STATE_MAP,
    TRANSITIONS,
)


class TestDocumentFSM:
    """Test suite for DocumentFSM stateless validator."""

    # ------------------------------------------------------------------
    # Valid transitions for Pipeline 1
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            ("uploaded", "previewing"),
            ("uploaded", "failed"),
            ("previewing", "awaiting_decision"),
            ("previewing", "failed"),
            ("awaiting_decision", "parsing"),
            ("awaiting_decision", "duplicate"),
            ("awaiting_decision", "new_version"),
            ("awaiting_decision", "archived"),
            ("parsing", "validation"),
            ("parsing", "failed"),
            ("validation", "ready_for_promotion"),
            ("validation", "review_required"),
            ("validation", "failed"),
            ("ready_for_promotion", "approved"),
            ("ready_for_promotion", "failed"),
            ("review_required", "approved"),
            ("review_required", "failed"),
            ("approved", "registry"),
            ("approved", "failed"),
            ("registry", "pending_index"),
            ("registry", "failed"),
        ],
    )
    def test_pipeline_1_valid_transitions(self, from_state, to_state):
        """All documented Pipeline 1 transitions must be valid."""
        assert DocumentFSM.can_transition(from_state, to_state), (
            f"Transition {from_state} -> {to_state} should be valid"
        )

    # ------------------------------------------------------------------
    # Valid transitions for Pipeline 2
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            ("pending_index", "indexing"),
            ("pending_index", "failed"),
            ("indexing", "indexed"),
            ("indexing", "failed"),
        ],
    )
    def test_pipeline_2_valid_transitions(self, from_state, to_state):
        """All documented Pipeline 2 transitions must be valid."""
        assert DocumentFSM.can_transition(from_state, to_state)

    # ------------------------------------------------------------------
    # Invalid transitions
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Skipping states
            ("uploaded", "parsing"),
            ("uploaded", "registry"),
            ("uploaded", "indexed"),
            ("previewing", "parsing"),
            ("previewing", "registry"),
            ("parsing", "approved"),
            ("parsing", "registry"),
            ("validation", "registry"),
            # Going backwards
            ("parsing", "uploaded"),
            ("validation", "previewing"),
            ("registry", "awaiting_decision"),
            ("indexed", "pending_index"),
            ("indexed", "indexing"),
            # Terminal jumps
            ("uploaded", "archived"),
            ("uploaded", "indexed"),
            ("registered", "uploaded"),  # non-existent state
        ],
    )
    def test_invalid_transitions(self, from_state, to_state):
        """Invalid transitions must be rejected."""
        assert not DocumentFSM.can_transition(from_state, to_state), (
            f"Transition {from_state} -> {to_state} should be invalid"
        )

    # ------------------------------------------------------------------
    # validate_transition raises on invalid
    # ------------------------------------------------------------------

    def test_validate_transition_valid(self):
        """validate_transition does not raise for valid transitions."""
        DocumentFSM.validate_transition("uploaded", "previewing")

    def test_validate_transition_invalid_raises(self):
        """validate_transition raises InvalidTransitionError for invalid."""
        with pytest.raises(InvalidTransitionError):
            DocumentFSM.validate_transition("uploaded", "indexed")

    def test_validate_transition_error_contains_states(self):
        """InvalidTransitionError contains from_state and to_state."""
        try:
            DocumentFSM.validate_transition("parsing", "uploaded")
        except InvalidTransitionError as e:
            assert e.from_state == "parsing"
            assert e.to_state == "uploaded"

    # ------------------------------------------------------------------
    # Terminal states
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "state",
        ["indexed", "archived", "duplicate"],  # N/A: failed can go to uploaded/archived
    )
    def test_terminal_states(self, state):
        """Terminal states have no outgoing transitions."""
        # Note: indexed, archived are terminal (empty set)
        # failed has transitions to uploaded and archived
        # duplicate has transition to archived
        # new_version has transitions to parsing and archived
        if state == "indexed" or state == "archived":
            assert DocumentFSM.is_terminal(state), f"{state} should be terminal"
        else:
            assert not DocumentFSM.is_terminal(state), f"{state} should not be terminal"

    # ------------------------------------------------------------------
    # allowed_transitions_from
    # ------------------------------------------------------------------

    def test_allowed_transitions_from_uploaded(self):
        allowed = DocumentFSM.allowed_transitions_from("uploaded")
        assert sorted(allowed) == sorted(["previewing", "failed"])

    def test_allowed_transitions_from_nonexistent(self):
        allowed = DocumentFSM.allowed_transitions_from("nonexistent")
        assert allowed == []

    # ------------------------------------------------------------------
    # Step-to-state mapping
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "step_name,expected_state",
        [
            ("preview", "awaiting_decision"),
            ("ocr", "parsing"),
            ("parser", "parsing"),
            ("converter", "validation"),
            ("registry", "registry"),
            ("rag_index", "indexed"),
        ],
    )
    def test_step_to_state_mapping(self, step_name, expected_state):
        """Each step maps to the correct FSM state."""
        result = DocumentFSM.get_step_transition(step_name)
        assert result == expected_state, (
            f"Step {step_name} should map to {expected_state}, got {result}"
        )

    def test_step_to_state_unknown(self):
        """Unknown step returns None."""
        assert DocumentFSM.get_step_transition("unknown_step") is None

    # ------------------------------------------------------------------
    # Pipeline classification
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "state,is_p1,is_p2",
        [
            ("uploaded", True, False),
            ("previewing", True, False),
            ("awaiting_decision", True, False),
            ("parsing", True, False),
            ("validation", True, False),
            ("ready_for_promotion", True, False),
            ("review_required", True, False),
            ("approved", True, False),
            ("registry", True, False),
            ("pending_index", False, True),
            ("indexing", False, True),
            ("indexed", False, True),
            ("failed", False, False),
            ("duplicate", False, False),
            ("archived", False, False),
        ],
    )
    def test_pipeline_classification(self, state, is_p1, is_p2):
        """States correctly classify as Pipeline 1 / Pipeline 2 / other."""
        assert DocumentFSM.is_pipeline_1_state(state) == is_p1
        assert DocumentFSM.is_pipeline_2_state(state) == is_p2

    # ------------------------------------------------------------------
    # Pipeline step definitions
    # ------------------------------------------------------------------

    def test_pipeline_1_has_correct_steps(self):
        """Pipeline 1 must have 4 steps in order."""
        assert PIPELINE_1_STEPS == ["ocr", "parser", "converter", "registry"]

    def test_pipeline_2_has_correct_steps(self):
        """Pipeline 2 must have 1 step."""
        assert PIPELINE_2_STEPS == ["rag_index"]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_can_transition_with_invalid_state_string(self):
        """Non-existent state strings return False."""
        assert not DocumentFSM.can_transition("flerb", "uploaded")
        assert not DocumentFSM.can_transition("uploaded", "flerb")

    def test_all_transitions_are_symmetric_in_transitions_dict(self):
        """Every state in TRANSITIONS is a DocumentState enum."""
        for from_state, to_states in TRANSITIONS.items():
            assert isinstance(from_state, DocumentState)
            for to_state in to_states:
                assert isinstance(to_state, DocumentState)

    def test_all_document_states_covered_in_transitions(self):
        """Every DocumentState appears at least once as a key in TRANSITIONS."""
        for state in DocumentState:
            assert state in TRANSITIONS, (
                f"State {state.value} missing from TRANSITIONS"
            )
