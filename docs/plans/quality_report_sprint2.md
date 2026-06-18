# Отчёт о качестве — Sprint 2 (17.06.2026)

> **Шаблон/заготовка** для регулярных отчётов о качестве RAG и OCR (P4-1).
> **Источник**: `5.docs_action_plan_17_06.md` P4-1, спринт 11.06–17.06.

## 1. Метрики RAG Search

| Метрика | Целевое значение (SLO) | Текущее | Статус |
|---------|------------------------|---------|--------|
| **Recall@10** (Sprint 2 baseline) | ≥ 0.85 | TBD (замер после Sprint 2) | 🟡 |
| **MRR@10** (Mean Reciprocal Rank) | ≥ 0.75 | TBD | 🟡 |
| **p50 latency** | ≤ 300 мс | TBD | 🟡 |
| **p95 latency** (SLO P4-5) | ≤ 500 мс | TBD | 🟡 |
| **p99 latency** | ≤ 1 с | TBD | 🟡 |

**Стратегия по умолчанию**: Vector+Rerank (S2) — Qwen3-Embedding-4B, VECTOR(2048), chunk 1024, rerank bge-reranker-v2-m3-int8 (TEI).

## 2. Метрики OCR/Parser

| Метрика | Целевое значение | Текущее | Статус |
|---------|------------------|---------|--------|
| **avg_confidence** (P12-2) | ≥ 0.85 для авто-завершения | TBD | 🟡 |
| **pages_failed rate** | ≤ 1% | TBD | 🟡 |
| **reprocess_required rate** | ≤ 5% | TBD | 🟡 |
| **operator_confirmation_required rate** | ≤ 15% | TBD | 🟡 |
| **Lama fallback rate** (P3-6) | ≤ 3% (только для не-конфиденциальных) | TBD | 🟡 |

## 3. Метрики пайплайнов

| Метрика | Целевое значение (SLO) | Текущее | Статус |
|---------|------------------------|---------|--------|
| Pipeline 1 (preview) | ≤ 30 с | TBD | 🟡 |
| Pipeline 1 (full) | ≤ 5 мин (для 100 страниц) | TBD | 🟡 |
| Pipeline 2 (indexing) p95 (SLO P4-5) | ≤ 60 с CPU / ≤ 15 с GPU | TBD | 🟡 |
| Pipeline 3 (search+LLM) | ≤ 3 с | TBD | 🟡 |

## 4. A/B-тесты

| Тест | Гипотеза | Статус |
|------|----------|--------|
| S2 vs S6 (Hybrid_RRF) | S2 имеет лучший Recall@10 | ⏳ запланирован Sprint 3 |
| Qwen3-Embedding-4B vs Qwen3-Embedding-8B | 4B быстрее, 8B точнее | ⏳ запланирован Sprint 3 |
| Chunk 1024 vs 2048 | 1024 — лучше recall, 2048 — лучше context | ⏳ запланирован Sprint 3 |

## 5. Замечания и риски

| Риск | Описание | Митигация |
|------|----------|-----------|
| **Recall < 0.85** | Низкое покрытие релевантных чанков | Увеличить `top_k`, попробовать MultiQuery (S3) |
| **p95 > 500 мс** | Медленный поиск | Увеличить кеш, оптимизировать pgvector индекс (IVFFlat → HNSW) |
| **Lama Parser > 3%** | Много fallback на облако | Для конфиденциальных — отключить Lama (P3-6), для остальных — увеличить долю локальных OCR-движков |

## 6. Связанные документы

- `docs/methodology/rag_experiments_methodology.md` — методология экспериментов.
- `docs/methodology/rag_evaluation_methodology.md` — метрики и протоколы оценки.
- `docs/architecture/monitoring.md` (NEW) — SLO/SLI (P11-7) и алерты (P11-8).
- `docs/api/rag_search_service_api.md` — конфигурация по умолчанию (P13-1).
- Sprint 2 план: `docs_plans/features/sprint2_11_06_17_06.md`.
