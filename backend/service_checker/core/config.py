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
        "port": 8080,
        "health_url": "http://127.0.0.1:8080/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.gateway:app",
            "--host", "127.0.0.1", "--port", "8081",
        ],
    },
    "auth": {
        "name": "Auth Service",
        "type": "mock",
        "port": 8082,
        "health_url": "http://127.0.0.1:8082/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.auth_service.main:app",
            "--host", "127.0.0.1", "--port", "8082",
        ],
    },
    "orchestrator": {
        "name": "Orchestrator Service",
        "type": "mock",
        "port": 8081,
        "health_url": "http://127.0.0.1:8081/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.orchestrator_service.main:app",
            "--host", "127.0.0.1", "--port", "8081",
        ],
    },
    "query": {
        "name": "Query Service",
        "type": "mock",
        "port": 8083,
        "health_url": "http://127.0.0.1:8083/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.query_service.main:app",
            "--host", "127.0.0.1", "--port", "8083",
        ],
    },
    "registry": {
        "name": "Registry Service",
        "type": "mock",
        "port": 8084,
        "health_url": "http://127.0.0.1:8084/api/v1/registry/classifiers/",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "mocks.registry_service.main:app",
            "--host", "127.0.0.1", "--port", "8084",
        ],
    },
    "integration": {
        "name": "Integration Service",
        "type": "real",
        "port": 8085,
        "health_url": "http://127.0.0.1:8085/api/v1/integration/",
        "cwd": BACKEND_DIR / "integration_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "8085",
        ],
    },
    "registry_real": {
        "name": "Registry Service (real)",
        "type": "real",
        "port": 8084,
        "health_url": "http://127.0.0.1:8084/api/v1/",
        "cwd": BACKEND_DIR / "registry_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "8084",
        ],
    },
    "parser": {
        "name": "Parser Service",
        "type": "real",
        "port": 8087,
        "health_url": "http://127.0.0.1:8087/health",
        "cwd": BACKEND_DIR / "parser_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "8087",
        ],
    },
    "rag_builder": {
        "name": "RAG Builder Service",
        "type": "real",
        "port": 8090,
        "health_url": "http://127.0.0.1:8090/api/v1/rag/",
        "cwd": BACKEND_DIR,
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "rag_builder.main:app",
            "--host", "127.0.0.1", "--port", "8090",
        ],
    },
    "rag_search": {
        "name": "RAG Search Service",
        "type": "real",
        "port": 8091,
        "health_url": "http://127.0.0.1:8091/",
        "cwd": BACKEND_DIR / "rag_search_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "8091",
        ],
    },
    "converter_validator": {
        "name": "Converter-Validator Service",
        "type": "real",
        "port": 8086,
        "health_url": "http://127.0.0.1:8086/api/v1/converter/",
        "cwd": BACKEND_DIR / "converter_validator_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "8086",
        ],
    },
    "ocr": {
        "name": "OCR Service",
        "type": "real",
        "port": 8088,
        "health_url": "http://127.0.0.1:8088/api/v1/",
        "cwd": BACKEND_DIR / "ocr_service",
        "run_cmd": lambda: [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "8088",
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
    "chat_inference": ["auth", "query", "rag_search"],
    "registry_lifecycle": ["auth", "registry"],
    "full_document_lifecycle": ["auth", "registry", "rag_builder", "rag_search"],
    "admin_user_lifecycle": ["auth", "query"],
    "registry_quarantine": ["auth", "registry"],
    "orchestrator_draft_lifecycle": ["auth", "orchestrator", "registry"],
    "multi_document_cross_search": ["minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"],
    "document_approval": ["orchestrator", "registry", "rag_builder", "rag_search"],
    "orchestrator_document_reject": ["auth", "orchestrator"],
    "orchestrator_metadata_update": ["auth", "orchestrator"],
    "orchestrator_draft_delete": ["auth", "orchestrator"],
    "orchestrator_document_reprocess": ["auth", "orchestrator", "registry"],
    "orchestrator_document_versions": ["auth", "orchestrator", "registry"],
    "orchestrator_full_document_lifecycle": ["auth", "orchestrator", "registry", "rag_builder", "rag_search"],
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
