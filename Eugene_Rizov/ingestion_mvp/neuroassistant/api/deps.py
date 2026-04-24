"""Dependency wiring for the FastAPI app."""

from __future__ import annotations

from functools import lru_cache

from neuroassistant.document_loader.pipeline import IngestionPipeline
from neuroassistant.repositories import InMemoryRepository
from neuroassistant.db import DbConfig
from neuroassistant.db import build_engine
from neuroassistant.db import build_sessionmaker
from neuroassistant.repositories_pg import PostgresRepository
from neuroassistant.storage.artifacts import LocalArtifactStorage


@lru_cache
def get_repo():
    # Default to Postgres if DATABASE_URL is set, otherwise in-memory.
    if "DATABASE_URL" in __import__("os").environ:
        session = get_session()
        return PostgresRepository(session=session)
    return InMemoryRepository()


@lru_cache
def get_engine():
    cfg = DbConfig.from_env()
    engine = build_engine(cfg)
    return engine


@lru_cache
def get_sessionmaker():
    return build_sessionmaker(get_engine())


def get_session():
    return get_sessionmaker()()


@lru_cache
def get_storage() -> LocalArtifactStorage:
    return LocalArtifactStorage.from_env()


@lru_cache
def get_pipeline() -> IngestionPipeline:
    return IngestionPipeline(repo=get_repo(), storage=get_storage())

