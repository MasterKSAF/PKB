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

# Реестр доступных пайплайнов: имя → класс
PIPELINE_REGISTRY: dict[str, type[PipelineDef]] = {
    "document_processing": DocumentProcessingPipeline,
    "chat_inference": ChatInferencePipeline,
    "registry_lifecycle": RegistryLifecyclePipeline,
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
    "PIPELINE_REGISTRY",
]
