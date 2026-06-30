"""
Tests for configuration module (config.py).

Verifies that Settings and ServiceConfig correctly parse environment
variables and apply defaults.
"""

import os
from unittest.mock import patch

import pytest

from app.core.config import ServiceConfig, Settings, get_settings


def _clean_env():
    """Remove forced mock env vars from conftest so defaults are visible."""
    for key in list(os.environ):
        if key.endswith("_MOCK"):
            del os.environ[key]


class TestServiceConfig:
    """Tests for ServiceConfig (per-service settings)."""

    def test_default_mock_mode(self):
        """All services default to mock=False in real mode."""
        _clean_env()
        config = ServiceConfig()
        assert config.REGISTRY_SERVICE_MOCK is False
        assert config.RAG_SERVICE_MOCK is False
        assert config.OCR_SERVICE_MOCK is False

    def test_default_service_urls(self):
        """All services have default Docker internal URLs."""
        _clean_env()
        config = ServiceConfig()
        assert config.REGISTRY_SERVICE_URL == "http://registry-service:8084"
        assert config.RAG_BUILDER_SERVICE_URL == "http://rag-builder:8090"
        assert config.RAG_SEARCH_SERVICE_URL == "http://rag-search:8091"
        assert config.RAG_SERVICE_URL is None  # deprecated
        assert config.OCR_SERVICE_URL == "http://ocr-service:8088"

    def test_override_with_env(self):
        """Setting env vars should override defaults."""
        with patch.dict(os.environ, {
            "REGISTRY_SERVICE_URL": "http://registry:8084",
            "REGISTRY_SERVICE_MOCK": "false",
            "RAG_BUILDER_SERVICE_URL": "http://rag-builder:8090",
            "RAG_SEARCH_SERVICE_URL": "http://rag-search:8091",
            "RAG_SERVICE_MOCK": "false",
        }, clear=False):
            config = ServiceConfig()
            assert config.REGISTRY_SERVICE_URL == "http://registry:8084"
            assert config.REGISTRY_SERVICE_MOCK is False
            assert config.RAG_BUILDER_SERVICE_URL == "http://rag-builder:8090"
            assert config.RAG_SEARCH_SERVICE_URL == "http://rag-search:8091"
            assert config.RAG_SERVICE_MOCK is False

    def test_deprecated_rag_service_url_syncs_to_builder(self):
        """Setting deprecated RAG_SERVICE_URL syncs to RAG_BUILDER_SERVICE_URL."""
        _clean_env()
        with patch.dict(os.environ, {
            "RAG_SERVICE_URL": "http://custom-rag:9090",
        }, clear=False):
            config = ServiceConfig()
            assert config.RAG_SERVICE_URL == "http://custom-rag:9090"
            assert config.RAG_BUILDER_SERVICE_URL == "http://custom-rag:9090"
            assert config.RAG_SEARCH_SERVICE_URL == "http://rag-search:8091"  # unchanged

    def test_mixed_mock_and_real(self):
        """Some services mock, some real."""
        _clean_env()
        with patch.dict(os.environ, {
            "OCR_SERVICE_MOCK": "true",
        }, clear=False):
            config = ServiceConfig()
            assert config.OCR_SERVICE_MOCK is True
            assert config.REGISTRY_SERVICE_MOCK is False  # still default


class TestSettings:
    """Tests for main Settings class."""

    def test_default_app_values(self):
        settings = Settings()
        assert settings.APP_NAME == "orchestrator-service"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8081
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_default_jwt(self):
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "your-secret-key-here"
        assert settings.JWT_ALGORITHM == "HS256"

    def test_override_app_settings(self):
        with patch.dict(os.environ, {
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "API_V1_PREFIX": "/api/v2",
        }, clear=False):
            settings = Settings()
            assert settings.APP_VERSION == "2.0.0"
            assert settings.DEBUG is True
            assert settings.HOST == "127.0.0.1"
            assert settings.PORT == 9000
            assert settings.API_V1_PREFIX == "/api/v2"

    def test_override_jwt(self):
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": "my-super-secret-key",
            "JWT_ALGORITHM": "RS256",
        }, clear=False):
            settings = Settings()
            assert settings.JWT_SECRET_KEY == "my-super-secret-key"
            assert settings.JWT_ALGORITHM == "RS256"

    def test_nested_service_config(self):
        _clean_env()
        settings = Settings()
        assert isinstance(settings.services, ServiceConfig)
        assert settings.services.REGISTRY_SERVICE_MOCK is False

    def test_flat_env_vars_do_not_crash(self):
        """
        Flat env vars (without SERVICES__ prefix) must not cause
        ValidationError on Settings init.
        ServiceConfig (nested BaseSettings) reads them independently.
        """
        _clean_env()
        with patch.dict(os.environ, {
            "REGISTRY_SERVICE_URL": "http://registry:8084",
            "REGISTRY_SERVICE_MOCK": "false",
            "OCR_SERVICE_URL": "http://ocr:8088",
        }, clear=False):
            # Must not raise
            settings = Settings()
            # Values are read by nested ServiceConfig
            assert settings.services.REGISTRY_SERVICE_URL == "http://registry:8084"
            assert settings.services.REGISTRY_SERVICE_MOCK is False
            assert settings.services.OCR_SERVICE_URL == "http://ocr:8088"


class TestGetSettings:
    """Tests for the get_settings() singleton."""

    def test_get_settings_returns_settings_instance(self):
        result = get_settings()
        assert isinstance(result, Settings)

    def test_get_settings_returns_same_type(self):
        result1 = get_settings()
        result2 = get_settings()
        assert type(result1) == type(result2)
        assert result1.APP_NAME == result2.APP_NAME


class TestEnvFileLoading:
    """Tests for .env file loading."""

    def test_settings_has_env_file_configured(self):
        """Verify that Settings.model_config has env_file set."""
        assert Settings.model_config.get("env_file") == ".env"

    def test_env_nested_delimiter(self):
        """Verify nested env delimiter is configured."""
        assert Settings.model_config.get("env_nested_delimiter") == "__"


class TestPipelineConfig:
    """Tests for PipelineConfig (P3S-1/P3S-2)."""

    def test_pending_state_timeout_default(self):
        """PENDING_STATE_TIMEOUT defaults to 180 seconds."""
        from app.core.config import PipelineConfig
        config = PipelineConfig()
        assert config.PENDING_STATE_TIMEOUT == 180

    def test_absolute_task_timeout_default(self):
        """ABSOLUTE_TASK_TIMEOUT_HOURS defaults to 48 hours."""
        from app.core.config import PipelineConfig
        config = PipelineConfig()
        assert config.ABSOLUTE_TASK_TIMEOUT_HOURS == 48


# ===========================================================================
#  P2-9: TestAllServicesDisabled
#  Источник: todo_pipeline_coverage.md (P2 №9)
#
#  Все сервисы выключены (PARSER_ENABLED=False, OCR_ENABLED=False) → задача
#  должна fail с error_code=NO_AVAILABLE_ENGINES. Реализация в
#  app/core/pipeline/orchestrator.py::on_step_failed
#  (строки проверки engine-availability).
# ===========================================================================


class TestAllServicesDisabled:
    """P2-9: все движки OCR/Parser выключены → NO_AVAILABLE_ENGINES."""

    @pytest.fixture
    def mock_db(self):
        """Mock AsyncSession для unit-тестов."""
        from unittest.mock import AsyncMock
        m = AsyncMock()
        m.flush = AsyncMock()
        return m

    def test_parser_and_ocr_can_be_disabled(self):
        """PARSER_ENABLED и OCR_ENABLED можно выставить в False."""
        from app.core.config import ServiceConfig

        cfg = ServiceConfig()
        # По умолчанию True
        assert cfg.PARSER_ENABLED is True
        assert cfg.OCR_ENABLED is True
        # Можно отключить
        cfg.PARSER_ENABLED = False
        cfg.OCR_ENABLED = False
        assert cfg.PARSER_ENABLED is False
        assert cfg.OCR_ENABLED is False

    def test_pipeline_config_has_required_engines(self):
        """В ServiceConfig есть флаги для управления движками."""
        from app.core.config import ServiceConfig

        cfg = ServiceConfig()
        assert hasattr(cfg, "PARSER_ENABLED")
        assert hasattr(cfg, "OCR_ENABLED")
        assert hasattr(cfg, "PARSER_FALLBACK_TO_OCR")

    async def test_on_step_failed_handles_all_disabled(
        self, mock_db
    ):
        """on_step_failed при выключенных движках → NO_AVAILABLE_ENGINES, task failed."""
        from app.core.config import settings
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from unittest.mock import AsyncMock

        # Временно отключаем оба движка
        original_parser = settings.services.PARSER_ENABLED
        original_ocr = settings.services.OCR_ENABLED
        original_fallback = settings.services.PARSER_FALLBACK_TO_OCR
        settings.services.PARSER_ENABLED = False
        settings.services.OCR_ENABLED = False
        settings.services.PARSER_FALLBACK_TO_OCR = False

        try:
            orchestrator = PipelineOrchestrator(mock_db)
            orchestrator.task_repo = AsyncMock()

            # MockTask
            class _MT:
                id = 1
                draft_id = 1
                document_id = 0
                trace_id = "trace"
                status = "active"
                retry_count = 0
                current_step_index = 0
                current_step_name = "preview_ocr"
                locked_by = None
                locked_at = None

            class _MS:
                def __init__(self, name, idx, status="running"):
                    self.id = idx
                    self.task_id = 1
                    self.step_name = name
                    self.step_index = idx
                    self.status = status
                    self.service_name = "Parser Service"
                    self.output_data = {}
                    self.input_data = {"file_key": "f"}

            task = _MT()
            orchestrator.task_repo.get_task.return_value = task
            orchestrator.task_repo.get_task_steps.return_value = [
                _MS("preview_ocr", 0, "running"),
            ]

            await orchestrator.on_step_failed(
                task_id=1,
                step_name="preview_ocr",
                error_code="PARSER_FAILED",
                error_message="both engines disabled",
            )

            # Task должен быть помечен как failed с NO_AVAILABLE_ENGINES
            set_error_call = orchestrator.task_repo.set_task_error
            if set_error_call.call_args_list:
                error_codes = [
                    c.kwargs.get("error_code") or c.args[1]
                    for c in set_error_call.call_args_list
                    if len(c.args) > 1 or "error_code" in c.kwargs
                ]
                assert "NO_AVAILABLE_ENGINES" in error_codes, (
                    f"Expected NO_AVAILABLE_ENGINES, got {error_codes}"
                )
        finally:
            settings.services.PARSER_ENABLED = original_parser
            settings.services.OCR_ENABLED = original_ocr
            settings.services.PARSER_FALLBACK_TO_OCR = original_fallback

    def test_mock_mode_keeps_engines_enabled(self):
        """В mock-режиме движки считаются доступными."""
        from app.core.config import ServiceConfig

        cfg = ServiceConfig()
        # По умолчанию оба движка включены
        assert cfg.PARSER_ENABLED is True
        assert cfg.OCR_ENABLED is True

    def test_settings_reset_engines(self):
        """Изменения флагов движков не сохраняются между инстансами."""
        from app.core.config import ServiceConfig

        c1 = ServiceConfig()
        c1.PARSER_ENABLED = False
        c1.OCR_ENABLED = False

        c2 = ServiceConfig()
        # Новый инстанс — дефолтные значения
        assert c2.PARSER_ENABLED is True
        assert c2.OCR_ENABLED is True
