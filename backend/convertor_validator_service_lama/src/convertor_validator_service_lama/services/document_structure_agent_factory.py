from __future__ import annotations

from dataclasses import dataclass

from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.contracts import LlamaExtractPassName
from convertor_validator_service_lama.models.extract_job import ExtractJobPollingConfig
from convertor_validator_service_lama.services.document_structure_prompt_agent import (
    DocumentStructurePromptAgent,
    DocumentStructurePromptAgentConfig,
)
from convertor_validator_service_lama.services.llama_extract_structured_json_backend import (
    LlamaExtractClientLike,
    LlamaExtractStructuredJsonPromptBackend,
    LlamaExtractStructuredJsonPromptBackendConfig,
)


@dataclass(frozen=True)
class LlamaExtractDocumentStructureAgentFactoryConfig:
    parse_job_id: str | None = None
    document_hint: str | None = None
    pass_name: LlamaExtractPassName = "sections"
    schema_name: str = "document_structure_extraction_v1"
    expand: list[str] | None = None
    polling_config: ExtractJobPollingConfig | None = None
    include_metadata_in_instructions: bool = True


@dataclass(frozen=True)
class LlamaExtractDocumentStructureAgentBundle:
    agent: DocumentStructurePromptAgent
    backend: LlamaExtractStructuredJsonPromptBackend

    def close(self) -> None:
        self.backend.close()


def build_llama_extract_document_structure_agent(
    *,
    settings: Settings | None = None,
    client: LlamaExtractClientLike | None = None,
    config: LlamaExtractDocumentStructureAgentFactoryConfig | None = None,
) -> LlamaExtractDocumentStructureAgentBundle:
    """Build DocumentStructurePromptAgent backed by LlamaExtract.

    This is a composition helper only. It does not run the workflow, does not
    create API endpoints, and does not perform network calls by itself.
    """

    resolved_config = config or LlamaExtractDocumentStructureAgentFactoryConfig()

    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=settings,
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id=resolved_config.parse_job_id,
            pass_name=resolved_config.pass_name,
            schema_name=resolved_config.schema_name,
            expand=resolved_config.expand,
            polling_config=resolved_config.polling_config,
            include_metadata_in_instructions=resolved_config.include_metadata_in_instructions,
        ),
    )

    agent = DocumentStructurePromptAgent(
        backend=backend,
        config=DocumentStructurePromptAgentConfig(
            document_hint=resolved_config.document_hint,
        ),
    )

    return LlamaExtractDocumentStructureAgentBundle(
        agent=agent,
        backend=backend,
    )
