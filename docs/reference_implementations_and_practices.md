# OKB: reference implementations and best practices

Updated: 2026-04-20

## What this note is for

This note benchmarks public implementations and product patterns that are closest to the OKB MVP:

- engineering and regulatory document corpus;
- OCR for scans and low-text PDFs;
- searchable chunked knowledge base;
- grounded answers with citations;
- versioned regulatory content;
- limited, review-oriented compliance checking instead of fully automatic engineering decisions.

The benchmark is based on the current OKB materials:

- `docs/knowledge_base_reading_report.md`
- `docs/mvp_12_week_plan.md`
- `docs/okb_mvp_presentation_notes.md`
- `docs/okb_mvp_tl_questions.md`

At the time of review, the local corpus already includes a large mixed-format knowledge base with many PDFs, scanned/low-text documents, registry-like sources, and classification / regulatory publications. That makes OKB much closer to a regulated engineering knowledge system than to a generic "chat over PDFs" product.

## Top 5 reference implementations

### 1. DNV RuleAgent + Rules and Standards Explorer

Why it is the closest reference:

- it is directly in the maritime / class-rules domain;
- it uses AI over official rule content;
- it keeps traceability back to the source system;
- it narrows retrieval using vessel context.

What matters for OKB:

- AI answers are not detached from the rule base;
- every answer links back to the authoritative source;
- edition-specific references are preserved;
- retrieval is narrowed by operational context, not only by keyword search.

Official references:

- DNV Rules and Standards Explorer: <https://www.dnv.cn/rules-standards/>
- DNV RuleAgent: <https://www.dnv.com/services/ruleagent/>

### 2. Bureau Veritas Rules Search / Rules Explorer

Why it matters:

- strong example of a digital regulatory corpus, not just a PDF dump;
- supports search by reference, topic and edition date;
- exposes latest updates and integrates with a broader compliance toolbox.

What matters for OKB:

- keep the rule base as a structured, filterable catalog;
- support search by code, topic, edition, and domain;
- show "latest updates" as a first-class object, not as a side effect;
- connect document search with adjacent engineering/compliance tools.

Official references:

- Rules & Guidelines: <https://marine-offshore.bureauveritas.com/rules-guidelines>
- Rules Search: <https://marine-offshore.bureauveritas.com/rules-search>
- BVCompliance: <https://marine-offshore.bureauveritas.com/bvcompliance>

### 3. ABS Rule Manager 2.0

Why it matters:

- focused implementation of searchable access to the latest requirements;
- built around an engineering rules library rather than generic enterprise search;
- emphasizes engaging with the most relevant content instead of browsing raw publications.

What matters for OKB:

- fast search over the full text of requirements;
- navigation centered on relevant engineering content;
- treat "rules library UX" as a separate product problem, not only a backend problem.

Official references:

- ABS Rules and Guides: <https://ww2.eagle.org/en/rules-and-resources/rules-and-guides-v2.html>
- Rule Manager 2.0 Quick Start Guide: <https://ww2.eagle.org/content/dam/eagle/rules-and-resources/RuleManager2/rule-manager-2-quick-start-guide.pdf>

### 4. OneOcean Regs4ships / MarineRegulations

Why it matters:

- very strong example of operational regulatory delivery, not only search;
- puts rules in a vessel-specific, version-controlled, always-updated library;
- supports offline access and change timelines, which is rare and valuable.

What matters for OKB:

- tailor regulatory sets to vessel / project / class / equipment context;
- maintain document histories and future amendment timelines;
- support offline or weak-connectivity workflows where required;
- expose auditability, latest updates, and inspection-ready views.

Official references:

- Regs4ships: <https://www.oneocean.com/how-we-help/grc/regs4ships>
- MarineRegulations brochure: <https://www.oneocean.com/wp-content/uploads/2025/09/OneOcean_MarineRegulations_Sept2025-1.pdf>
- Regs4ships module guide: <https://page.oneocean.com/rs/009-WDD-596/images/LR_OneOcean_RegulatoryCompliance_Regs4ships_ModuleGuide_FINAL.pdf?version=0>

### 5. Microsoft Azure AI Search + Document Intelligence + OpenAI On Your Data

Why it matters:

- strongest public blueprint for the technical side of the OKB MVP;
- directly covers OCR, chunking, hybrid retrieval, citations, ACL-aware retrieval, and complex-question decomposition.

What matters for OKB:

- OCR and layout extraction must be first-class, not an afterthought;
- chunking is tunable and materially affects answer quality;
- document-level access control should be implemented in retrieval, not only in UI;
- multi-query retrieval is useful for broad engineering questions that have multiple "asks";
- citations need correct field mapping, not just prompt instructions.

Official references:

- Azure Document Intelligence overview: <https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview>
- Azure OpenAI "use your data": <https://learn.microsoft.com/en-us/azure/foundry-classic/openai/concepts/use-your-data>
- Azure AI Search agentic retrieval: <https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview>

## Bonus reference

### Google Document AI + Document AI Warehouse + Vertex AI Search

Why it is useful:

- combines OCR, document warehouse, grounded summaries, ACLs, and enterprise search;
- especially relevant where OKB will need both governed document storage and answer generation.

Official references:

- Document AI overview: <https://cloud.google.com/document-ai>
- Document AI Warehouse generative search blog: <https://cloud.google.com/blog/products/ai-machine-learning/mobilize-your-unstructured-data-with-generative-ai>
- Vertex AI Search summaries and citations: <https://docs.cloud.google.com/generative-ai-app-builder/docs/get-search-summaries>
- Vertex AI Search access control: <https://docs.cloud.google.com/generative-ai-app-builder/docs/data-source-access-control>

## Best practices that fit OKB directly

### 1. Build a document registry before building the assistant

The best references do not treat the corpus as a loose folder of files. They maintain a registry with version, source, applicability, publication date, and status. For OKB this is mandatory because your own MVP notes already identify source registries, duplicate handling, and working-vs-archival versions as core risks.

### 2. Keep answers grounded in an authoritative source system

The strongest pattern is not "LLM over files", but "LLM over a governed source layer". DNV is the clearest example: the AI layer points back to the official rules explorer. OKB should do the same for RKO / GOST / internal project documents.

### 3. Make citations a product feature, not a backend detail

Every factual answer should carry:

- source document;
- edition / version if known;
- page;
- fragment or chunk;
- confidence or insufficiency note when evidence is weak.

This matches the current OKB MVP scope and should remain non-negotiable.

### 4. Use hybrid retrieval, not vector-only retrieval

For engineering and regulatory texts, exact reference search matters:

- document codes;
- clause numbers;
- standard identifiers;
- ship / equipment terms;
- abbreviations and transliterated variants.

The search layer should combine lexical, metadata, and semantic retrieval.

### 5. Chunk by structure where possible

The public technical stacks increasingly support semantic chunking or structure-aware chunking. For OKB, the preferred order is:

1. clause / paragraph / section chunking for normative documents;
2. page-aware chunking for PDFs and scans;
3. table-aware extraction for specs and registries;
4. fallback fixed-size chunking only when structure is unavailable.

### 6. Treat OCR quality as metadata

Your corpus already contains low-text PDFs, scans, and DWG-related gaps. Best practice is to store OCR confidence and extraction status per file or page, then surface weak-quality evidence in the UI and answer pipeline.

### 7. Separate "search answer" from "engineering decision"

The right pattern for OKB is the same one your MVP documents already describe:

- the system may highlight a possible mismatch;
- the system must not issue final engineering approval;
- ambiguous cases must be escalated to human review.

This is exactly how a safe engineering assistant should be positioned.

### 8. Tailor relevance using project or vessel context

DNV and OneOcean show that relevance improves dramatically when the system knows context. OKB should be able to narrow retrieval by:

- project;
- vessel type;
- class;
- applicable rule family;
- equipment domain;
- working edition date;
- source authority.

### 9. Expose change history and future changes

Regulatory content is alive. The best systems show:

- latest updates;
- version history;
- upcoming amendments;
- current vs archived content.

For OKB, this is more important than a fancy chat UI.

### 10. Design for adjacent workflows, not only Q&A

The benchmarked systems are useful because they support real work:

- inspection readiness;
- compliance preparation;
- update tracking;
- vessel- or context-specific libraries;
- operational search;
- guided review.

OKB should therefore support at least three user modes:

- document search / registry mode;
- cited answer mode;
- comparison / review mode.

## What I would adopt first in OKB

### Immediate priorities

1. Create a normalized document registry with authoritative version flags.
2. Add structural metadata at document, page, and chunk levels.
3. Preserve exact source references for every answer.
4. Implement hybrid retrieval with metadata filters.
5. Surface OCR / extraction quality in both indexing and answer generation.

### Second wave

1. Add context-aware retrieval by project / vessel / rule family.
2. Add change-history and "latest update" views.
3. Introduce limited parameter-check workflows with `OK`, `WARNING`, and `POTENTIAL_MISMATCH`.
4. Add ACL-aware retrieval if the corpus will be shared across teams or projects.

## Short conclusion

The strongest public analog is DNV RuleAgent because it is closest to the OKB domain and product shape. The strongest technical implementation pattern is Microsoft Azure's document + search + grounded retrieval stack. The operational compliance benchmark is OneOcean Regs4ships / MarineRegulations. Together, these references suggest that OKB should be built as a governed engineering knowledge system with traceability, version control, hybrid retrieval, and human-in-the-loop review, not as a generic PDF chatbot.
