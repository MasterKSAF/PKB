"""Postgres database wiring (SQLAlchemy 2.0).

This module is used to persist ingestion metadata (documents, runs, errors,
events) so reports do not depend on in-memory state or filesystem parsing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker


class Base(DeclarativeBase):
    pass


@dataclass(frozen=True, slots=True)
class DbConfig:
    database_url: str

    @classmethod
    def from_env(cls) -> "DbConfig":
        url = os.environ.get("DATABASE_URL")
        if not url:
            # Example: postgresql+psycopg://user:pass@localhost:5432/neuroassistant
            url = "postgresql+psycopg://postgres:postgres@localhost:5432/neuroassistant"
        return cls(database_url=url)


def build_engine(cfg: DbConfig) -> Engine:
    # psycopg uses libpq; connect_timeout is in seconds.
    return create_engine(
        cfg.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def build_sessionmaker(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)

