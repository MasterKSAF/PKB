"""
PKB Neuroassistant — Service Checker Configuration.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List


# ── Project paths ────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GATEWAY_DIR = PROJECT_ROOT / "backend" / "gateway_service"
BACKEND_DIR = PROJECT_ROOT / "backend"

DOCKER_DIR = BACKEND_DIR / "service_checker" / "docker"
DOCKER_COMPOSE_FILE = DOCKER_DIR / "docker-compose.yml"
DOCKERFILE_PATH = DOCKER_DIR / "Dockerfile"

# ── Service definitions ──────────────────────────────────────────────

SERVICE_DEFS: Dict[str, Dict[str, Any]] = {
    "gateway": {
        "name": "Gateway (Mock All-in-One)",
        "type": "mock",
        "port": 18080,
        "health_url": "http://127.0.0.1:18080/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.gateway:app",
            "--host", "127.0.0.1", "--port", "18081",
        ],
    },
    "auth": {
        "name": "Auth Service",
        "type": "mock",
        "port": 18082,
        "health_url": "http://127.0.0.1:18082/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.auth_service.main:app",
            "--host", "127.0.0.1", "--port", "18082",
        ],
    },
    "orchestrator": {
        "name": "Orchestrator Service",
        "type": "mock",
        "port": 18081,
        "health_url": "http://127.0.0.1:18081/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.orchestrator_service.main:app",
            "--host", "127.0.0.1", "--port", "18081",
        ],
    },
    "query": {
        "name": "Query Service",
        "type": "mock",
        "port": 18083,
        "health_url": "http://127.0.0.1:18083/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.query_service.main:app",
            "--host", "127.0.0.1", "--port", "18083",
        ],
    },
    "registry": {
        "name": "Registry Service",
        "type": "mock",
        "port": 18084,
        "health_url": "http://127.0.0.1:18084/api/v1/registry/classifiers/",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.registry_service.main:app",
            "--host", "127.0.0.1", "--port", "18084",
        ],
    },
    "integration": {
        "name": "Integration Service",
        "type": "real",
        "port": 18085,
        "health_url": "http://127.0.0.1:18085/api/v1/integration/",
        "cwd": BACKEND_DIR / "integration_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "18085",
        ],
    },
    "registry_real": {
        "name": "Registry Service (real)",
        "type": "real",
        "port": 18084,
        "health_url": "http://127.0.0.1:18084/api/v1/",
        "cwd": BACKEND_DIR / "registry_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "18084",
        ],
    },
    "parser": {
        "name": "Parser Service",
        "type": "real",
        "port": 18087,
        "health_url": "http://127.0.0.1:18087/health",
        "cwd": BACKEND_DIR / "parser_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "18087",
        ],
    },
    "rag_builder": {
        "name": "RAG Builder Service",
        "type": "real",
        "port": 18090,
        "health_url": "http://127.0.0.1:18090/api/v1/rag/",
        "cwd": BACKEND_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "rag_builder.main:app",
            "--host", "127.0.0.1", "--port", "18090",
        ],
    },
    "rag_search": {
        "name": "RAG Search Service",
        "type": "real",
        "port": 18091,
        "health_url": "http://127.0.0.1:18091/",
        "cwd": BACKEND_DIR / "rag_search_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "18091",
        ],
    },
    "converter_validator": {
        "name": "Converter-Validator Service",
        "type": "real",
        "port": 18086,
        "health_url": "http://127.0.0.1:18086/api/v1/converter/",
        "cwd": BACKEND_DIR / "converter_validator_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "18086",
        ],
    },
    "ocr": {
        "name": "OCR Service",
        "type": "real",
        "port": 18088,
        "health_url": "http://127.0.0.1:18088/api/v1/",
        "cwd": BACKEND_DIR / "ocr_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "18088",
        ],
    },
}

# ── Test data ────────────────────────────────────────────────────────

TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}

HEADERS_JSON = {"Content-Type": "application/json", "Accept": "application/json"}

# ── Docker service names (for display) ──────────────────────────────

DOCKER_SERVICE_NAMES = {
    "postgres": "PostgreSQL + pgvector",
    "redis": "Redis (cache + broker)",
    "minio": "MinIO (S3-совместимое хранилище)",
    "tei": "TEI (Text Embeddings Inference)",
    "app": "Python-сервисы (11 процессов под supervisord)",
}

# ── Pipeline -> service mapping для сводной таблицы ─────────────────

PIPELINE_SERVICE_MAP = {
    "document_processing": ["minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"],
    "chat_inference": ["rag_search"],
    "registry_lifecycle": ["registry"],
    "full_document_lifecycle": ["registry", "rag_builder", "rag_search"],
    "admin_user_lifecycle": ["query"],
    "registry_quarantine": ["registry"],
    "orchestrator_draft_lifecycle": ["orchestrator", "registry"],
    "multi_document_cross_search": ["minio", "parser", "converter_validator", "rag_builder", "rag_search"],
    "document_approval": ["orchestrator", "rag_builder"],
    "orchestrator_document_reject": ["orchestrator"],
    "orchestrator_metadata_update": ["orchestrator"],
    "orchestrator_draft_delete": ["orchestrator"],
    "orchestrator_document_reprocess": ["orchestrator", "registry"],
    "orchestrator_document_versions": ["orchestrator", "registry"],
    "orchestrator_full_document_lifecycle": ["orchestrator", "registry", "rag_builder", "rag_search"],
    "full_document_cycle": ["orchestrator", "rag_builder", "rag_search"],
}

PIPELINE_SERVICE_COLUMNS = {
    "document_processing": "Documents",
    "chat_inference": "Chat",
    "registry_lifecycle": "Registry",
    "full_document_lifecycle": "Lifecycle",
    "admin_user_lifecycle": "AdminUsers",
    "registry_quarantine": "Quarantine",
    "orchestrator_draft_lifecycle": "Orchestrator",
    "multi_document_cross_search": "MultiDoc",
    "orchestrator_document_reject": "OrchReject",
    "orchestrator_metadata_update": "OrchMetadata",
    "orchestrator_draft_delete": "OrchDelete",
    "orchestrator_document_reprocess": "OrchReprocess",
    "orchestrator_document_versions": "OrchVersions",
    "orchestrator_full_document_lifecycle": "OrchFull",
}

SERVICE_DISPLAY_NAMES = {
    "gateway": "Gateway",
    "orchestrator": "Orchestrator",
    "auth": "Auth Service",
    "query": "Query Service",
    "registry": "Registry Service",
    "converter_validator": "Converter-Validator",
    "parser": "Parser Service",
    "rag_builder": "RAG Builder",
    "rag_search": "RAG Search",
    "tei": "TEI",
    "minio": "MinIO",
    "integration": "Integration Service",
    "ocr": "OCR Service",
}
