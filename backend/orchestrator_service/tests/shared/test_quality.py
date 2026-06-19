"""
Tests for quality assessment thresholds (T-1).

Verifies:
  1. score < 0.6 → "critical"
  2. 0.6 ≤ score < 0.85 → "warning"
  3. score ≥ 0.85 → "ok"
  4. Boundary values at 0.6 and 0.85
  5. Monotonicity: higher score never produces worse severity
"""

import pytest

from app.shared.quality import assess_quality, assess_notifications


class TestAssessQualityBoundaries:
    """Exact boundary value tests."""

    def test_below_critical(self):
        """Score just below 0.6 → critical."""
        assert assess_quality(0.599) == "critical"
        assert assess_quality(0.0) == "critical"
        assert assess_quality(0.5) == "critical"

    def test_warning_range(self):
        """Score in warning range → warning."""
        assert assess_quality(0.6) == "warning"
        assert assess_quality(0.7) == "warning"
        assert assess_quality(0.84) == "warning"

    def test_ok_range(self):
        """Score in ok range → ok."""
        assert assess_quality(0.85) == "ok"
        assert assess_quality(0.95) == "ok"
        assert assess_quality(1.0) == "ok"

    def test_scores_above_one(self):
        """Scores > 1.0 are still ok (saturated)."""
        assert assess_quality(1.5) == "ok"


class TestAssessQualityMonotonicity:
    """Monotonicity: higher score never returns worse severity."""

    SEVERITY_ORDER = {"critical": 0, "warning": 1, "ok": 2}

    @pytest.mark.parametrize("low,high", [
        (0.3, 0.7),    # critical → warning
        (0.5, 0.6),    # critical → warning
        (0.7, 0.9),    # warning → ok
        (0.3, 0.9),    # critical → ok
        (0.6, 0.85),   # warning → ok
        (0.0, 1.0),    # extreme
    ])
    def test_monotonic_pairs(self, low, high):
        """For low < high, severity(low) must not be better than severity(high)."""
        sev_low = self.SEVERITY_ORDER[assess_quality(low)]
        sev_high = self.SEVERITY_ORDER[assess_quality(high)]
        assert sev_low <= sev_high, f"Monotonicity broken: {low} -> {sev_low}, {high} -> {sev_high}"


class TestAssessNotifications:
    """Tests for assess_notifications helper."""

    def test_critical_has_notification(self):
        """Critical score yields a notification with critical severity."""
        notes = assess_notifications(0.3)
        assert len(notes) == 1
        assert notes[0]["severity"] == "critical"
        assert notes[0]["code"] == "low_quality"

    def test_warning_has_notification(self):
        """Warning score yields a notification with warning severity."""
        notes = assess_notifications(0.7)
        assert len(notes) == 1
        assert notes[0]["severity"] == "warning"
        assert notes[0]["code"] == "degraded_quality"

    def test_ok_empty_notifications(self):
        """Ok score yields no notifications."""
        notes = assess_notifications(0.95)
        assert len(notes) == 0
