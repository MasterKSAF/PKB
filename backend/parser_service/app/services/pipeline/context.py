"""
Контекст выполнения пайплайна. Передаётся между шагами.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from app.services.parsers.base import ParseResult


@dataclass
class ProcessingContext:
    """
    Содержит всю информацию о текущей обработке.
    Поля заполняются шагами по мере выполнения.
    """
    task_id: int
    version_id: str
    file_key: str
    options: Dict[str, bool] = field(default_factory=dict)

    file_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None
    parse_result: Optional[ParseResult] = None
    final_json: Optional[Dict[str, Any]] = None
    max_pages: Optional[int] = None
    original_file_name: str = ""   # оригинальное имя файла (без пути)