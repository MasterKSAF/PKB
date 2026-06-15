#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline Testing (Сквозные сценарии)

Пакет содержит реализацию сквозных бизнес-пайплайнов обработки документов.
"""

from __future__ import annotations

from .base import (
    PipelineContext,
    PipelineResult,
    PipelineStep,
    PipelineRunner,
    StepStatus,
    PipelineDef,
)

from .document_processing import DocumentProcessingPipeline
from .chat_inference import ChatInferencePipeline
from .registry_lifecycle import RegistryLifecyclePipeline
from .full_document_lifecycle import FullDocumentLifecyclePipeline
from .admin_user_lifecycle import AdminUserLifecyclePipeline
from .registry_quarantine import RegistryQuarantinePipeline
from .orchestrator_draft_lifecycle import OrchestratorDraftLifecyclePipeline
from .multi_document_cross_search import MultiDocumentCrossSearchPipeline

# Реестр доступных пайплайнов: имя → класс
PIPELINE_REGISTRY: dict[str, type[PipelineDef]] = {
    "document_processing": DocumentProcessingPipeline,
    "chat_inference": ChatInferencePipeline,
    "registry_lifecycle": RegistryLifecyclePipeline,
    "full_document_lifecycle": FullDocumentLifecyclePipeline,
    "admin_user_lifecycle": AdminUserLifecyclePipeline,
    "registry_quarantine": RegistryQuarantinePipeline,
    "orchestrator_draft_lifecycle": OrchestratorDraftLifecyclePipeline,
    "multi_document_cross_search": MultiDocumentCrossSearchPipeline,
}

__all__ = [
    "PipelineContext",
    "PipelineResult",
    "PipelineStep",
    "PipelineRunner",
    "StepStatus",
    "PipelineDef",
    "DocumentProcessingPipeline",
    "ChatInferencePipeline",
    "RegistryLifecyclePipeline",
    "FullDocumentLifecyclePipeline",
    "AdminUserLifecyclePipeline",
    "RegistryQuarantinePipeline",
    "OrchestratorDraftLifecyclePipeline",
    "MultiDocumentCrossSearchPipeline",
    "PIPELINE_REGISTRY",
]
