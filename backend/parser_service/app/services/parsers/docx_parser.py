"""
Заглушка парсера для DOCX (Office Open XML).
"""
from typing import Dict, Any
from app.services.parsers.base import BaseParser, ParseResult


class DocxParser(BaseParser):
    async def parse(self, file_bytes: bytes, options: Dict[str, bool]) -> ParseResult:
        # TODO: Реализовать парсер для .docx
        return ParseResult(
            full_json={"error": "DOCX parser not implemented"},
            images=[],
            total_pages=0
        )