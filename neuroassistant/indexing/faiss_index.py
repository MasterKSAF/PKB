"""Minimal FAISS indexing for ingested documents (MVP).

This is NOT the final RAG indexing design. It exists to satisfy the MVP request
to have a real vector index (FAISS) built from ingested artifacts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    ingestion_id: str
    text: str


def simple_embed(texts: list[str], dim: int = 256) -> np.ndarray:
    # Deterministic hashing-based embedding (no external model dependency).
    # Upgrade path: replace with real embeddings.
    vecs = np.zeros((len(texts), dim), dtype="float32")
    for i, t in enumerate(texts):
        for token in t.split():
            h = hash(token) % dim
            vecs[i, h] += 1.0
        n = np.linalg.norm(vecs[i])
        if n > 0:
            vecs[i] /= n
    return vecs


def build_faiss_index(chunks: list[Chunk], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    texts = [c.text for c in chunks]
    emb = simple_embed(texts)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    faiss.write_index(index, str(out_dir / "index.faiss"))
    meta = [c.__dict__ for c in chunks]
    (out_dir / "chunks.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"chunks": len(chunks), "dim": dim, "path": str(out_dir)}

