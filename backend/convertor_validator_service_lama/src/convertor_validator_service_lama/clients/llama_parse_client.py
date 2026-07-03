from typing import Any

from convertor_validator_service_lama.core.settings import Settings


class LlamaParseClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_parse_payload(self, source_pdf_path: str) -> dict[str, Any]:
        return {
            "source_pdf_path": source_pdf_path,
            "result_format": self._settings.parse_result_format,
            "base_url": self._settings.parse_base_url,
        }
