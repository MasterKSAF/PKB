import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def validate_classifiers(
    classification: dict[str, Any],
) -> dict[str, Any]:
    if not settings.registry_service_url:
        return _local_classifier_status(classification)

    url = (
        f"{settings.registry_service_url.rstrip('/')}"
        "/registry/classifiers/validate"
    )
    try:
        async with httpx.AsyncClient(
            timeout=settings.registry_timeout_sec
        ) as client:
            response = await client.post(url, json={"classification": classification})
            response.raise_for_status()
            body = response.json()
            data = body.get("data") or body
            return {
                "mks_oks_code": classification.get("mks_oks_code"),
                "mks_status": data.get("mks_status", "CONFIRMED"),
                "okstu_status": data.get("okstu_status", "NOT_USED"),
                "udk_code": classification.get("udk_code"),
                "udk_valid": data.get("udk_valid", True),
                "overall_status": _map_overall(data.get("overall_status")),
            }
    except Exception as exc:
        logger.warning("Registry classifier validation failed: %s", exc)
        return _local_classifier_status(classification)


def _map_overall(registry_status: str | None) -> str:
    if registry_status in ("valid", "CONFIRMED"):
        return "CONFIRMED"
    if registry_status in ("invalid", "PENDING_REVIEW"):
        return "PENDING_REVIEW"
    return "CONFIRMED"


def _local_classifier_status(
    classification: dict[str, Any],
) -> dict[str, Any]:
    mks = classification.get("mks_oks_code")
    return {
        "mks_oks_code": mks,
        "mks_status": "CONFIRMED" if mks else "NOT_FOUND",
        "okstu_status": (
            "NOT_USED"
            if not classification.get("okstu_code")
            else "CONFIRMED"
        ),
        "udk_code": classification.get("udk_code"),
        "udk_valid": True,
        "overall_status": "CONFIRMED" if mks else "PENDING_REVIEW",
    }
