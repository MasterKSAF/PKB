#!/usr/bin/env python3
"""Test search queries against the running service."""
import json
import urllib.request
import sys

BASE_URL = "http://127.0.0.1:8091/api/v1/rag/search"

def search(query, top_k=5, search_type="hybrid", rerank=True):
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps({
            "query": query,
            "top_k": top_k,
            "search_type": search_type,
            "rerank": rerank,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())


def print_results(data):
    print(f"Query: {data['query']}")
    print(f"Search type: {data['search_type_used']}")
    print(f"Total found: {data['total_found']}")
    print(f"Processing time: {data['processing_time_ms']}ms")
    print()
    for i, ch in enumerate(data["results"], 1):
        print(f"--- Result #{i} (score: {ch['score']:.4f}) ---")
        print(f"  Doc: {ch['doc_code']} — {ch['document_title']}")
        print(f"  Section: {ch['section_title']} (clause {ch['clause']})")
        print(f"  Content: {ch['content'][:120]}...")
        print()


if __name__ == "__main__":
    queries = [
        "сварка стыковых соединений разделка кромок",
        "допуски метрической резьбы посадки с зазором",
        "ограждения движущихся частей оборудования",
    ]

    for q in queries:
        print("=" * 70)
        data = search(q)
        print_results(data)
        print()
