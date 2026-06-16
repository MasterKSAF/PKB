# tests/manual/test_openai_embeddings.py
# scripts/test_openai_embeddings.py

from rag_builder.embeddings.factory import build_embedding_provider


def main() -> None:

    provider = build_embedding_provider()

    print(
        f"Provider: {type(provider).__name__}"
    )

    # embedding = provider.create_embedding(
    #     "ГОСТ 20868-81"
    # )
    #
    # print(
    #     f"Dimension: {len(embedding)}"
    # )
    #
    # print(
    #     f"First 5 values: {embedding[:5]}"
    # )
    result = provider.create_embedding_with_usage("ГОСТ 20868-81")

    print(f"Provider: {type(provider).__name__}")
    print(f"Dimension: {len(result.embedding)}")
    print(f"Tokens: {result.token_count}")
    print(f"Cost USD: {result.cost_usd}")
    print(f"First 5 values: {result.embedding[:5]}")

if __name__ == "__main__":
    main()