"""
Document State Machine (FSM) — manages valid state transitions
for Pipeline 1 (formation) and Pipeline 2 (indexation).

All valid FSM states and transitions are defined as data structures.
The FSM is stateless: it validates transitions but actual state
is persisted in the Document model via FOR UPDATE locking.
"""

from enum import Enum


class DocumentState(str, Enum):
    """All possible FSM states for a document."""

    # Pipeline 1 — Formation
    UPLOADED = "uploaded"
    PREVIEWING = "previewing"
    AWAITING_DECISION = "awaiting_decision"
    PARSING = "parsing"
    VALIDATION = "validation"
    READY_FOR_PROMOTION = "ready_for_promotion"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REGISTRY = "registry"

    # Pipeline 2 — Indexation
    PENDING_INDEX = "pending_index"
    INDEXING = "indexing"
    INDEXED = "indexed"

    # Terminal / special states
    FAILED = "failed"
    DUPLICATE = "duplicate"
    NEW_VERSION = "new_version"
    ARCHIVED = "archived"


# Valid transitions: from_state -> set of allowed to_states
TRANSITIONS: dict[DocumentState, set[DocumentState]] = {
    # Pipeline 1
    DocumentState.UPLOADED: {
        DocumentState.PREVIEWING,
        DocumentState.FAILED,
    },
    DocumentState.PREVIEWING: {
        DocumentState.AWAITING_DECISION,
        DocumentState.FAILED,
    },
    DocumentState.AWAITING_DECISION: {
        DocumentState.PARSING,
        DocumentState.DUPLICATE,
        DocumentState.NEW_VERSION,
        DocumentState.ARCHIVED,
    },
    DocumentState.PARSING: {
        DocumentState.VALIDATION,
        DocumentState.FAILED,
    },
    DocumentState.VALIDATION: {
        DocumentState.READY_FOR_PROMOTION,
        DocumentState.REVIEW_REQUIRED,
        DocumentState.FAILED,
    },
    DocumentState.READY_FOR_PROMOTION: {
        DocumentState.APPROVED,
        DocumentState.FAILED,
    },
    DocumentState.REVIEW_REQUIRED: {
        DocumentState.APPROVED,
        DocumentState.FAILED,
    },
    DocumentState.APPROVED: {
        DocumentState.REGISTRY,
        DocumentState.FAILED,
    },
    DocumentState.REGISTRY: {
        DocumentState.PENDING_INDEX,
        DocumentState.FAILED,
    },
    # Pipeline 2
    DocumentState.PENDING_INDEX: {
        DocumentState.INDEXING,
        DocumentState.FAILED,
    },
    DocumentState.INDEXING: {
        DocumentState.INDEXED,
        DocumentState.FAILED,
    },
    # Terminal states: no outgoing transitions
    DocumentState.INDEXED: set(),
    DocumentState.FAILED: {
        DocumentState.UPLOADED,  # reprocess: retry after fix
        DocumentState.ARCHIVED,
    },
    DocumentState.DUPLICATE: {
        DocumentState.ARCHIVED,
    },
    DocumentState.NEW_VERSION: {
        DocumentState.PARSING,  # start pipeline for new version
        DocumentState.ARCHIVED,
    },
    DocumentState.ARCHIVED: set(),
}

# Step-to-state mapping: which FSM state to enter when a step completes
STEP_TO_STATE_MAP: dict[str, DocumentState] = {
    "preview": DocumentState.AWAITING_DECISION,
    "ocr": DocumentState.PARSING,
    "parser": DocumentState.PARSING,
    "converter": DocumentState.VALIDATION,
    "registry": DocumentState.REGISTRY,
    "rag_index": DocumentState.INDEXED,
}

# Pipeline definitions: ordered step names for each pipeline
PIPELINE_1_STEPS = ["ocr", "parser", "converter", "registry"]
PIPELINE_2_STEPS = ["rag_index"]


class InvalidTransitionError(ValueError):
    """Raised when an invalid FSM transition is attempted."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid FSM transition: {from_state} -> {to_state}")


class DocumentFSM:
    """Stateless FSM validator for document state transitions."""

    @staticmethod
    def can_transition(from_state: str, to_state: str) -> bool:
        """Check if a transition is valid."""
        try:
            from_enum = DocumentState(from_state)
            to_enum = DocumentState(to_state)
        except ValueError:
            return False
        return to_enum in TRANSITIONS.get(from_enum, set())

    @staticmethod
    def validate_transition(from_state: str, to_state: str) -> None:
        """Validate transition; raise InvalidTransitionError if invalid."""
        if not DocumentFSM.can_transition(from_state, to_state):
            raise InvalidTransitionError(from_state, to_state)

    @staticmethod
    def allowed_transitions_from(state: str) -> list[str]:
        """Return list of allowed target states from a given state."""
        try:
            state_enum = DocumentState(state)
        except ValueError:
            return []
        return [s.value for s in TRANSITIONS.get(state_enum, set())]

    @staticmethod
    def is_terminal(state: str) -> bool:
        """Check if a state is terminal (no outgoing transitions)."""
        return len(DocumentFSM.allowed_transitions_from(state)) == 0

    @staticmethod
    def is_pipeline_1_state(state: str) -> bool:
        """Check if state belongs to Pipeline 1."""
        p1_states = {
            "uploaded", "previewing", "awaiting_decision", "parsing",
            "validation", "ready_for_promotion", "review_required",
            "approved", "registry",
        }
        return state in p1_states

    @staticmethod
    def is_pipeline_2_state(state: str) -> bool:
        """Check if state belongs to Pipeline 2."""
        return state in {"pending_index", "indexing", "indexed"}

    @staticmethod
    def get_step_transition(step_name: str) -> str | None:
        """Get the FSM state that should be entered after a step completes."""
        state = STEP_TO_STATE_MAP.get(step_name)
        return state.value if state else None
