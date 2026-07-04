from typing import Any

from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.contracts import LlamaExtractPassName


class LlamaExtractClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_extract_payload(
        self,
        parse_job_id: str,
        pass_name: LlamaExtractPassName,
    ) -> dict[str, Any]:
        return {
            "parse_job_id": parse_job_id,
            "pass_name": pass_name,
            "base_url": self._settings.extract_base_url,
        }
