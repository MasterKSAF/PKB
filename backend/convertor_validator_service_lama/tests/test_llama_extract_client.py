from convertor_validator_service_lama.clients.llama_extract_client import LlamaExtractClient
from convertor_validator_service_lama.core.settings import Settings


def test_llama_extract_client_builds_payload_from_parse_job_id() -> None:
    settings = Settings()
    client = LlamaExtractClient(settings)

    payload = client.build_extract_payload(
        parse_job_id="parse-job-123",
        pass_name="sections",
    )

    assert payload == {
        "parse_job_id": "parse-job-123",
        "pass_name": "sections",
        "base_url": "https://api.cloud.llamaindex.ai",
    }
