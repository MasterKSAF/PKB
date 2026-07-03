from convertor_validator_service_lama.core.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.service_name == "convertor_validator_service_lama"
    assert settings.environment == "local"
    assert settings.cloud_api_key is None
    assert settings.parse_base_url == "https://api.cloud.llamaindex.ai"
    assert settings.extract_base_url == "https://api.cloud.llamaindex.ai"
    assert settings.parse_result_format == "markdown"


def test_settings_reads_lama_env_prefix(monkeypatch) -> None:
    monkeypatch.setenv("LAMA_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("LAMA_PARSE_RESULT_FORMAT", "json")

    settings = Settings()

    assert settings.cloud_api_key == "test-key"
    assert settings.parse_result_format == "json"
