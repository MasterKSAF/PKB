from convertor_validator_service_lama.clients.llama_parse_client import LlamaParseClient
from convertor_validator_service_lama.core.settings import Settings


def test_llama_parse_client_builds_parse_payload() -> None:
    settings = Settings(parse_result_format="json")
    client = LlamaParseClient(settings)

    payload = client.build_parse_payload("D:/tmp/source.pdf")

    assert payload == {
        "source_pdf_path": "D:/tmp/source.pdf",
        "result_format": "json",
        "base_url": "https://api.cloud.llamaindex.ai",
    }
