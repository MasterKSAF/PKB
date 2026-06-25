# Fix: IVFFlat → HNSW для vector-индекса в rag_builder

- [x] 1. Alembic migration — заменить ivfflat на hnsw
- [x] 2. service_checker/db_check.py — заменить rag_has_ivfflat на rag_has_hnsw
- [x] 3. Документация db_diagrams.md (3 копии) — IVFFlat → HNSW
- [x] 4. Документация ddl_migrations_17_06.md (3 копии) — IVFFlat → HNSW
