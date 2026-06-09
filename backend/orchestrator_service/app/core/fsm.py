"""
Draft State Machine (FSM) — manages valid state transitions for drafts,
and utility enumerations for pipeline Task status and stage.

The FSM is stateless: it validates transitions but actual state
is persisted via the Registry service (drafts) or the database (tasks).
"""

from enum import Enum


class DraftState(str, Enum):
    """All possible FSM states for a draft."""

    UPLOADED = "uploaded"
    PREVIEWING = "previewing"
    READY_FOR_APPROVE = "ready_for_approve"
    APPROVED = "approved"
    DISCARDED = "discarded"


# Valid transitions: from_state -> set of allowed to_states
DRAFT_TRANSITIONS: dict[DraftState, set[DraftState]] = {
    DraftState.UPLOADED: {DraftState.PREVIEWING},
    DraftState.PREVIEWING: {DraftState.READY_FOR_APPROVE},
    DraftState.READY_FOR_APPROVE: {DraftState.APPROVED, DraftState.DISCARDED},
    # Terminal states
    DraftState.APPROVED: set(),
    DraftState.DISCARDED: set(),
}


class DraftFSM:
    """Stateless FSM validator for draft state transitions."""

    @staticmethod
    def can_transition(from_state: str, to_state: str) -> bool:
        """Check if a transition is valid."""
        try:
            from_enum = DraftState(from_state)
            to_enum = DraftState(to_state)
        except ValueError:
            return False
        return to_enum in DRAFT_TRANSITIONS.get(from_enum, set())

    @staticmethod
    def validate_transition(from_state: str, to_state: str) -> None:
        """Validate transition; raise ValueError if invalid."""
        if not DraftFSM.can_transition(from_state, to_state):
            raise ValueError(
                f"Invalid draft FSM transition: {from_state} -> {to_state}"
            )

    @staticmethod
    def allowed_transitions_from(state: str) -> list[str]:
        """Return list of allowed target states from a given state."""
        try:
            state_enum = DraftState(state)
        except ValueError:
            return []
        return [s.value for s in DRAFT_TRANSITIONS.get(state_enum, set())]

    @staticmethod
    def is_terminal(state: str) -> bool:
        """Check if a state is terminal (no outgoing transitions)."""
        return len(DraftFSM.allowed_transitions_from(state)) == 0


class TaskStatus(str, Enum):
    """Status of a pipeline task."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStage(str, Enum):
    """Stage of a pipeline task lifecycle."""

    UPLOAD = "upload"
    PREVIEW = "preview"
    DECISION = "decision"
    FULL = "full"
    REGISTRY = "registry"
    INDEXATION = "indexation"
