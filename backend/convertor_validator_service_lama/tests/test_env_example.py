from pathlib import Path


def test_env_example_documents_lama_settings() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "LAMA_CLOUD_API_KEY=" in env_example
    assert "LAMA_PARSE_BASE_URL=" in env_example
    assert "LAMA_EXTRACT_BASE_URL=" in env_example
    assert "LAMA_PARSE_RESULT_FORMAT=" in env_example
