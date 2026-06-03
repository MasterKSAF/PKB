from __future__ import annotations

from collections.abc import Iterable

from rag_builder.models.contracts import ProtectedSpan, Section
from rag_builder.models.domain import Chunk
from loguru import logger
from rag_builder.core.config import settings


class ChunkingService:
    def build_chunks(
        self, document_id: str, sections: list[Section], protected_spans: list[ProtectedSpan], strategy: str
    ) -> list[Chunk]:
        logger.info(
            "Chunking start document_id={} sections={} strategy={}",
            document_id,
            len(sections),
            strategy,
        )
        span_map = {s.section_id: (s.start_offset, s.end_offset) for s in protected_spans}
        chunks: list[Chunk] = []
        for section in sections:
            logger.debug(
                "Chunking section start section_id={} type={} path={}",
                section.section_id,
                section.type,
                section.path,
            )
            chunk_texts = self._render_section_chunks(section, span_map.get(section.section_id))
            for idx, text in enumerate(chunk_texts):
                chunks.append(
                    Chunk(
                        section_id=section.section_id,
                        document_id=section.document_id,
                        chunk_index=idx,
                        content=text,
                        strategy=strategy,
                        page=section.page,
                    )
                )
            logger.debug("Chunking section done section_id={} chunks={}", section.section_id, len(chunk_texts))
        logger.info("Chunking done document_id={} total_chunks={}", document_id, len(chunks))
        return chunks

    def _render_section_chunks(self, section: Section, protected_span: tuple[int, int] | None) -> list[str]:
        if section.type == "table":
            return [self._table_to_markdown(section.content)]
        if section.type == "image":
            return [f"{section.content.get('caption', '')}\n{section.content.get('description', '')}".strip()]
        if section.type == "formula":
            return [f"{section.content.get('latex', '')}\n{section.content.get('meaning', '')}".strip()]
        text = str(section.content.get("text", "")).strip()
        return self._split_tokens(text, settings.chunk_max_tokens, protected_span)

    def _split_tokens(self, text: str, max_tokens: int, protected_span: tuple[int, int] | None) -> list[str]:
        words = text.split()
        if len(words) <= max_tokens:
            return [text] if text else []
        out: list[str] = []
        i = 0
        while i < len(words):
            j = min(i + max_tokens, len(words))
            if protected_span is not None:
                raw = " ".join(words[i:j])
                if len(raw) < protected_span[1] and j < len(words):
                    j = min(j + 1, len(words))
            out.append(" ".join(words[i:j]))
            i = j
        return out

    def _table_to_markdown(self, content: dict[str, object]) -> str:
        columns_obj = content.get("columns", [])
        rows_obj = content.get("rows", [])
        columns: Iterable[dict[str, object]] = columns_obj if isinstance(columns_obj, list) else []
        rows: Iterable[dict[str, object]] = rows_obj if isinstance(rows_obj, list) else []
        cols = [str(c.get("header", c.get("name", ""))) for c in columns]
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for row in rows:
            cells_obj = row.get("cells", {})
            cells: dict[str, object] = cells_obj if isinstance(cells_obj, dict) else {}
            vals = []
            for col in columns:
                name = str(col.get("name"))
                cell_obj = cells.get(name, {})
                cell: dict[str, object] = cell_obj if isinstance(cell_obj, dict) else {}
                vals.append(str(cell.get("label", cell.get("value", ""))))
            lines.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines)
