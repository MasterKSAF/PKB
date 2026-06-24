"""
Quality assessment utilities for Parser/OCR processing.

Maps processing quality scores to severity levels.
"""


def assess_quality(score: float) -> str:
    """Assess processing quality score and return severity.

    Thresholds (PS-4/OC-5):
        score < 0.6   → "critical"  — unusable quality
        0.6 ≤ score < 0.85 → "warning"  — degraded quality, needs review
        score ≥ 0.85  → "ok"        — acceptable quality

    Args:
        score: Quality score from 0.0 to 1.0.

    Returns:
        Severity level: "critical", "warning", or "ok".
    """
    if score < 0.6:
        return "critical"
    if score < 0.85:
        return "warning"
    return "ok"


def assess_notifications(score: float) -> list[dict]:
    """Build quality notifications list from score.

    Returns a list of notification dicts with code, message, severity.
    """
    severity = assess_quality(score)
    notifications = []

    if severity == "critical":
        notifications.append({
            "code": "low_quality",
            "message": f"Processing quality is critically low ({score:.2f})",
            "severity": "critical",
        })
    elif severity == "warning":
        notifications.append({
            "code": "degraded_quality",
            "message": f"Processing quality is below threshold ({score:.2f})",
            "severity": "warning",
        })

    return notifications
