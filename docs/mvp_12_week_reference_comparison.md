# OKB MVP: 12-week comparison with reference solutions

Updated: 2026-04-20

## Purpose

This note compares the current OKB 12-week MVP plan with the strongest public reference solutions reviewed on 2026-04-20.

The goal is not to copy external products as-is, but to make each OKB week explicit in three dimensions:

- what is already accepted as the OKB baseline;
- what the strongest reference implementations do in the same area;
- what should be adopted into OKB now, deferred, or deliberately left out of MVP.

Primary internal baseline:

- `docs/mvp_12_week_plan.md`
- `docs/reference_implementations_and_practices.md`

Reference shorthand used below:

- `DNV` = DNV RuleAgent + Rules and Standards Explorer
- `BV` = Bureau Veritas Rules Search / Rules Explorer
- `ABS` = ABS Rule Manager 2.0
- `OO` = OneOcean Regs4ships / MarineRegulations
- `AZ` = Azure AI Search + Document Intelligence + OpenAI On Your Data

## Weekly comparison

| Week | What is already accepted in OKB | What the reference solutions do | Decision for OKB |
|---|---|---|---|
| 1 | Freeze scope, inventory datasets, define source registry model, choose OCR/parser/embedding/storage baseline. | `DNV`, `BV`, `OO` all start from governed source collections, not loose files. `BV` and `OO` treat edition and update state as first-class data. `AZ` requires explicit field mapping, index shape, and access model. | Keep week 1 focused on corpus governance. Add mandatory fields: `source_authority`, `edition_date`, `authoritative_version`, `applicability_scope`, `document_status`, `processing_status`. This is now part of the accepted baseline, not a later enhancement. |
| 2 | Start ingestion: local folders, registry spreadsheets, text-first extraction, file type detection. | `AZ` and Google-style stacks treat OCR/layout as a document understanding layer, not only raw text extraction. `DNV` and `ABS` assume already-curated digital rule content. `OO` assumes controlled document distribution. | Keep OKB's MVP choice of text-first extraction plus OCR fallback for speed and budget, but add stronger metadata capture during ingestion: source lineage, edition hints, duplicate candidates, and page-level status. |
| 3 | OCR low-text PDFs, preserve page traceability, parse tables and page artifacts, mark failures for reprocessing. | `AZ` Document Intelligence emphasizes text, tables, layout, and key/value structure. `OO` and `DNV` show the value of reliable, usable content over raw ingestion volume. | Add per-page extraction confidence, low-text flags, OCR route, and structured artifacts for tables / title blocks where possible. Maintain a reprocessing queue and a visible list of problem files. |
| 4 | Build the knowledge base: normalize text, split into chunks, attach metadata, create embeddings, build index. | `AZ` uses chunked indexed content with mapped citation fields. `BV` and `ABS` show that exact rule references and edition filters matter. `DNV` keeps edition-specific rule navigation. | Adopt hybrid retrieval as the week-4 default: lexical + metadata + semantic. Preferred chunking order: clause/section, then page-aware chunks, then table-aware fragments, then fallback fixed-size chunks. |
| 5 | Retrieval and RAG answers with citations, source constraints, and control-set evaluation. | `DNV` links answers back to official rule sources. `AZ` shows citation quality depends on proper field mapping and chunk size. `OO` shows value of version history and latest updates in regulatory use. | Tighten the OKB answer contract: every factual answer must carry document, page, fragment/chunk, and insufficiency note if evidence is weak. Add tuning loop for chunk size based on control questions and citation quality. |
| 6 | Dialog layer: engineer-style questions, clarification when query is broad, short context retention. | `AZ` agentic retrieval decomposes multi-part questions into focused subqueries. `DNV` narrows relevance using vessel context. `OO` narrows content by vessel and operational applicability. | Keep a simple dialog MVP, but add context filters to the conversation model: project, vessel type, rule family, document set, edition period. Multi-query retrieval should be optional and used only for broad or compound questions. |
| 7 | Start decision checking: extract candidate parameters from drawings/specs and find related normative requirements. | `AZ` provides structure extraction and custom field models. `DNV` and `OO` suggest that domain context sharply improves relevance. None of the strong references position AI as a final engineering decision-maker. | Restrict week 7 to a small formalized set of parameters: material, thickness, mass, class, designation, selected numeric values. Every extracted parameter must preserve exact source location. |
| 8 | Compare project values against normative requirements and classify as `OK`, `WARNING`, or `POTENTIAL_MISMATCH`. | `DNV`, `BV`, and `OO` are strong on traceability, version awareness, and professional verification. Public best practice avoids automated final approval language in regulated workflows. | Preserve the current OKB rule: comparison is an engineer-review aid only. Add explicit display of both sides: requirement fragment, project fragment, normalized value/unit, and reason for ambiguity where present. |
| 9 | Formalize imports and integrations: local folder, spreadsheets, RKO corpus, Google Drive corpus; normalize metadata and duplicates. | `OO` is strong on update propagation and context-specific distribution. `BV` connects rule search to a larger compliance toolchain. `AZ` supports document-level access trimming and reusable indexes. | Keep MVP integrations limited, but strengthen the adapter model: source type, sync mode, version strategy, duplicate keys, and future ACL field. Add a placeholder for "latest update lane" even if full automation comes later. |
| 10 | Start frontend: document registry, status, search/chat, cited answer view, source preview, comparison result view. | `ABS` shows that rules-library UX matters on its own. `BV` offers search by reference, topic, and edition. `DNV` emphasizes source traceability. `OO` emphasizes audit/inspection readiness. | Structure the UI around three working modes: registry mode, cited answer mode, comparison/review mode. Filters should include source, code, edition, project, and processing state from day one. |
| 11 | Continue frontend and start testing: retrieval top-k, citation coverage, OCR quality, UI acceptance flows. | `AZ` explicitly ties retrieval quality to index design, chunking, and field mapping. `OO` focuses on inspection readiness and update clarity. `DNV` and `ABS` show the importance of trust in the evidence path. | Make evaluation visible: control queries, top-3 relevance, citation completeness, OCR failure log, and latency. Add a small expert-reviewed benchmark set rather than relying on subjective demo impressions. |
| 12 | Finish frontend, deployment, testing, and repeatable demo setup. | `OO` adds offline/low-connectivity value. `AZ` is strong on reproducible architecture and access control. `DNV` and `BV` show the value of stable authoritative navigation rather than flashy chat-only UX. | Keep deployment simple and reproducible. Freeze a demo corpus, document import commands, and ensure repeatable cited answers. Offline mode can remain deferred, but source preview, version visibility, and error visibility should be in the MVP demo. |

## What is now considered adopted into the OKB baseline

These are the strongest decisions that should no longer be treated as optional nice-to-haves:

- registry before assistant: the corpus must be governed before the chat layer is trusted;
- authoritative versioning: each document needs source and edition semantics where available;
- hybrid retrieval: exact code search and semantic search must coexist;
- structure-aware chunking: clause, page, and table structure should drive chunking;
- citation contract: document, page, fragment, and insufficiency note are mandatory;
- OCR quality metadata: low-text, OCR path, confidence, and extraction failure must be visible;
- review-only comparison: no final engineering approval/rejection language in MVP;
- context narrowing: project, vessel type, rule family, and source scope should reduce noise.

## What is recommended but can be deferred past MVP

- document-level ACL enforcement in retrieval, if the first MVP runs on a trusted internal corpus;
- automated regulatory update propagation from all sources;
- full vessel-specific or project-specific dynamic libraries;
- offline library mode similar to `OO`;
- advanced multi-query planning on every request;
- deep custom extraction models for many drawing/spec families.

## Where OKB should deliberately differ from the reference solutions

OKB should not overreach into areas that the current corpus and MVP do not support well yet:

- no promise of native DWG semantic understanding in MVP;
- no promise of final engineering conclusions;
- no broad generic enterprise assistant positioning;
- no overbuilt integration layer before the registry and cited search are stable;
- no heavy agent behavior if the evidence layer is still weak.

## Recommended reading order for implementation

1. `docs/mvp_12_week_plan.md`
2. This comparison note
3. `docs/reference_implementations_and_practices.md`

## Short conclusion

The current OKB plan is directionally sound. The biggest upgrade from the benchmark is not "more AI", but stricter source governance, better retrieval design, clearer citation guarantees, and a more explicit review workflow. In practical terms, the best external solutions suggest that OKB should spend its early weeks making the corpus trustworthy, versioned, filterable, and page-traceable, and only then layer dialog and comparison on top.
