"""
Заглушка парсера для DOC (Microsoft Word 97-2003).
"""
from typing import Dict, Any
from app.services.parsers.base import BaseParser, ParseResult


class DocParser(BaseParser):
    async def parse(self, file_bytes: bytes, options: Dict[str, bool]) -> ParseResult:
        # TODO: Реализовать парсер для .doc
        return ParseResult(
            full_json={"error": "DOC parser not implemented", "file_size_bytes": len(file_bytes)},
            images=[],
            total_pages=0
        )