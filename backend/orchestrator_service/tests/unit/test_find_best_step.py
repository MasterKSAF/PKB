"""
Unit tests for PipelineOrchestrator._find_best_step static method (H2).

Tests the step selection logic: prefers completed > running > pending.
"""

from app.core.pipeline.orchestrator import PipelineOrchestrator


class MockStep:
    """Minimal mock for TaskStep duck-typing."""
    def __init__(self, step_name: str, status: str):
        self.step_name = step_name
        self.status = status


class TestFindBestStep:
    """_find_best_step selects the best step by status priority."""

    def test_prefers_completed_over_running(self):
        """Completed step is preferred over running."""
        steps = [
            MockStep("preview_ocr", "pending"),
            MockStep("preview_ocr", "running"),
            MockStep("preview_ocr", "completed"),
        ]
        result = PipelineOrchestrator._find_best_step(steps, "preview_ocr")
        assert result is not None
        assert result.status == "completed"

    def test_prefers_running_over_pending(self):
        """Running step is preferred over pending."""
        steps = [
            MockStep("preview_ocr", "pending"),
            MockStep("preview_ocr", "running"),
        ]
        result = PipelineOrchestrator._find_best_step(steps, "preview_ocr")
        assert result is not None
        assert result.status == "running"

    def test_falls_back_to_pending(self):
        """Only pending step is returned if that's all there is."""
        steps = [MockStep("preview_ocr", "pending")]
        result = PipelineOrchestrator._find_best_step(steps, "preview_ocr")
        assert result is not None
        assert result.status == "pending"

    def test_returns_none_when_no_match(self):
        """No matching step name returns None."""
        steps = [MockStep("preview_ocr", "completed")]
        result = PipelineOrchestrator._find_best_step(steps, "nonexistent")
        assert result is None

    def test_ignores_other_step_names(self):
        """Steps with different names are ignored."""
        steps = [
            MockStep("upload", "completed"),
            MockStep("preview_ocr", "failed"),
            MockStep("preview_converter", "running"),
        ]
        result = PipelineOrchestrator._find_best_step(steps, "preview_ocr")
        assert result is not None
        assert result.status == "failed"

    def test_empty_steps_returns_none(self):
        """Empty list returns None."""
        result = PipelineOrchestrator._find_best_step([], "anything")
        assert result is None
