# src/rag_builder/chunking/service.py

from typing import Any

from rag_builder.models.contracts import BuildRequest, Section
from rag_builder.models.domain import Chunk


class ChunkingService:
    """
    Преобразует контейнер Registry (BuildRequest)
    во внутренние объекты Chunk.

    Текущая реализация MVP:

        1 Section -> 1 Chunk

    В будущем:

        1 Section -> N Chunks

    после внедрения нарезки по длине текста,
    количеству токенов и другим стратегиям.

    Важная задача сервиса:
    не потерять данные, необходимые для цитирования:

        - document_id
        - document_version_id
        - section_id
        - clause
        - page
        - bbox
        - references
    """
    MAX_CHUNK_CHARS = 2000
    OVERLAP_RATIO = 0.2

    # def _split_text(
    #         self,
    #         text: str,
    # ) -> list[str]:
    #
    #     text = text.strip()
    #
    #     if len(text) <= self.MAX_CHUNK_CHARS:
    #         return [text]
    #
    #     chunks: list[str] = []
    #
    #     start = 0
    #
    #     while start < len(text):
    #         end = start + self.MAX_CHUNK_CHARS
    #
    #         if end >= len(text):
    #             chunks.append(text[start:])
    #             break
    #
    #         split_pos = text.rfind(" ", start, end)
    #
    #         if split_pos <= start:
    #             split_pos = end
    #
    #         chunks.append(
    #             text[start:split_pos].strip()
    #         )
    #
    #         start = split_pos
    #
    #     return chunks

    def _split_text(
            self,
            text: str,
    ) -> list[str]:
        text = text.strip()

        if len(text) <= self.MAX_CHUNK_CHARS:
            return [text]

        chunks: list[str] = []

        start = 0
        overlap_chars = int(self.MAX_CHUNK_CHARS * self.OVERLAP_RATIO)

        while start < len(text):
            hard_end = min(start + self.MAX_CHUNK_CHARS, len(text))

            if hard_end >= len(text):
                tail = text[start:].strip()
                if tail:
                    chunks.append(tail)
                break

            split_pos = self._find_split_position(
                text=text,
                start=start,
                hard_end=hard_end,
            )

            chunk_text = text[start:split_pos].strip()

            if chunk_text:
                chunks.append(chunk_text)

            next_start = max(
                split_pos - overlap_chars,
                start + 1,
            )

            # Сдвигаем старт к ближайшему пробелу,
            # чтобы не начинать новый чанк с середины слова.
            while (
                    next_start < len(text)
                    and next_start > 0
                    and not text[next_start - 1].isspace()
            ):
                next_start += 1

            start = next_start

        return chunks

    def _find_split_position(
            self,
            text: str,
            start: int,
            hard_end: int,
    ) -> int:
        sentence_endings = [". ", "! ", "? ", ".\n", "!\n", "?\n"]

        best_sentence_pos = -1

        for marker in sentence_endings:
            pos = text.rfind(marker, start, hard_end)

            if pos > best_sentence_pos:
                best_sentence_pos = pos + len(marker)

        min_reasonable_end = start + int(self.MAX_CHUNK_CHARS * 0.5)

        if best_sentence_pos >= min_reasonable_end:
            return best_sentence_pos

        space_pos = text.rfind(" ", start, hard_end)

        if space_pos > start:
            return space_pos

        return hard_end


    def build_chunks(self, request: BuildRequest) -> list[Chunk]:
        """
        Главная точка входа.

        Получает контейнер Registry и создаёт список Chunk.

        На текущем этапе каждая Section превращается
        в один Chunk.
        """

        chunks: list[Chunk] = []

        for section in request.sections:

            # Приводим содержимое секции
            # к индексируемому тексту.
            content = self._render_section_content(section)

            # Пустые секции не индексируем.
            if not content:
                continue

            # Переносим все данные,
            # необходимые для будущего цитирования.
            subchunks = self._split_text(content)

            for chunk_index, subcontent in enumerate(subchunks):
                chunk = Chunk(
                    document_id=request.metadata.document_id,
                    document_version_id=request.metadata.document_version_id,

                    section_id=section.section_id,
                    parent_id=section.parent_id,

                    clause=section.clause,
                    path=section.path,

                    page=section.page,
                    bbox=section.bbox,

                    chunk_index=chunk_index,

                    chunk_type=section.type,

                    content=subcontent,

                    metadata=self._build_chunk_metadata(section),
                )

                chunks.append(chunk)

        return chunks

    def _render_section_content(self, section: Section) -> str:
        """
        Преобразует различные типы секций
        в текст для индексации и эмбеддингов.
        """

        if section.type in {"text", "textBlock", "headerFooter"}:
            return str(section.content.get("text", "")).strip()

        if section.type == "list":
            return self._render_list(section.content)

        if section.type == "table":
            return self._render_table(section.content)

        if section.type == "image":
            return self._render_image(section.content)

        if section.type == "formula":
            return self._render_formula(section.content)

        return ""

    def _render_list(self, content: dict[str, Any]) -> str:
        """
        Преобразует список в текст.

        Пример:

            - латунь
            - сталь
            - алюминиевый сплав
        """

        markdown = content.get("markdown")
        if markdown:
            return str(markdown).strip()

        items = content.get("items")

        if isinstance(items, list):
            return "\n".join(f"- {item}" for item in items)

        return ""

    def _render_table(self, content: dict[str, Any]) -> str:
        """
        Преобразует таблицу в Markdown.

        Это позволяет индексировать содержимое таблицы
        обычным текстовым поиском и эмбеддингами.
        """
        headers = content.get("headers")
        rows = content.get("rows")

        if isinstance(headers, list) and isinstance(rows, list):

            lines = [
                "| " + " | ".join(map(str, headers)) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
            ]

            for row in rows:
                if isinstance(row, list):
                    lines.append(
                        "| " + " | ".join(map(str, row)) + " |"
                    )

            return "\n".join(lines)

        markdown = content.get("markdown")

        if markdown:
            return str(markdown).strip()

        columns = content.get("columns", [])
        rows = content.get("rows", [])

        if not isinstance(columns, list) or not isinstance(rows, list):
            return ""

        headers = [str(col.get("header", col.get("name", ""))) for col in columns]

        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]

        for row in rows:
            cells = row.get("cells", {}) if isinstance(row, dict) else {}
            values = []

            for col in columns:
                name = str(col.get("name", ""))
                cell = cells.get(name, {}) if isinstance(cells, dict) else {}

                if isinstance(cell, dict):
                    value = cell.get("label", cell.get("value", ""))
                else:
                    value = cell

                values.append(str(value))

            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    def _render_image(self, content: dict[str, Any]) -> str:
        """
        Формирует индексируемое представление изображения.

        В будущем image_key будет ссылаться
        на объект в MinIO.
        """

        parts = [
            content.get("caption"),
            content.get("description"),
            content.get("image_key"),
        ]

        return "\n".join(str(part).strip() for part in parts if part)

    def _render_formula(self, content: dict[str, Any]) -> str:
        """
        Формирует текстовое представление формулы.

        Используются:
            - markdown
            - latex
            - смысл формулы
            - описание параметров
        """

        parts = [
            content.get("markdown"),
            content.get("latex"),
            content.get("meaning"),
        ]

        parameters = content.get("parameters")

        if isinstance(parameters, list):
            for parameter in parameters:
                if isinstance(parameter, dict):
                    symbol = parameter.get("symbol", "")
                    description = parameter.get("description", "")
                    unit = parameter.get("unit", "")

                    parts.append(
                        f"{symbol} — {description} {unit}".strip()
                    )

        return "\n".join(str(part).strip() for part in parts if part)

    def _build_chunk_metadata(self, section: Section) -> dict[str, Any]:
        """
        Формирует метаданные чанка.

        Здесь хранятся данные,
        которые не попадают в индексируемый текст,
        но могут понадобиться позже.
        """

        metadata: dict[str, Any] = {
            "section_type": section.type,
            "title": section.title,
            "references": [ref.model_dump() for ref in section.references],
        }

        # Для сложных объектов сохраняем
        # исходную структуру контейнера.
        if section.type in {"table", "image", "formula", "list"}:
            metadata["raw_content"] = section.content

        return metadata