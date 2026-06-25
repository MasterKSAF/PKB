# Fix: IVFFlat → HNSW для vector-индекса в rag_builder

- [x] 1. Alembic migration — заменить ivfflat на hnsw
- [x] 2. service_checker/db_check.py — заменить rag_has_ivfflat на rag_has_hnsw
- [x] 3. Документация db_diagrams.md (3 копии) — IVFFlat → HNSW
- [x] 4. Документация ddl_migrations_17_06.md (3 копии) — IVFFlat → HNSW
- [x] 5. Исправлен оператор: vector_cosine_ops → halfvec_cosine_ops (несовместим с halfvec)
- [x] 6. Исправлена версия pgvector: 0.7.0 → 0.4.2
- [x] 7. Исправлен импорт: Halfvec → HALFVEC
