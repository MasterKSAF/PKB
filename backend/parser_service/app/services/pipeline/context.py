"""
Контекст выполнения пайплайна. Передаётся между шагами.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from app.services.parsers.base import ParseResult


@dataclass
class ProcessingContext:
    """
    Контекст, через который шаги пайплайна обмениваются данными.

    Attributes:
        task_id: ID задачи
        draft_id: ID черновика
        file_key: Ключ файла в MinIO
        options: Опции парсинга (extract_tables, extract_images и т.д.)
        file_bytes: Содержимое файла (заполняется на шаге Download)
        mime_type: MIME-тип файла (заполняется на Validate)
        parse_result: Результат работы парсера
        final_json: Нормализованный и стандартизированный JSON
        max_pages: Ограничение по страницам (для preview)
        original_file_name: Оригинальное имя файла
        track_progress: Нужно ли обновлять progress в task_store (True для FULL, False для PREVIEW)
        preview_not_supported: Флаг, что preview не поддерживается (если max_pages < total_pages)
        total_pages: Общее количество страниц в документе
        temp_dir: Временная директория парсера (для очистки)
        shutdown_event: Событие для graceful shutdown
        api_version: Версия API (1 или 2), влияет на формат результата
        quality_code: Код качества PDF (из анализатора)
    """
    task_id: int
    draft_id: int
    file_key: str
    options: Dict[str, bool] = field(default_factory=dict)

    file_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None
    parse_result: Optional[ParseResult] = None
    final_json: Optional[Dict[str, Any]] = None
    max_pages: Optional[int] = None
    original_file_name: str = ""
    track_progress: bool = True
    preview_not_supported: bool = False
    total_pages: Optional[int] = None
    temp_dir: Optional[str] = None
    shutdown_event: Optional[object] = None
    api_version: int = 2
    quality_code: Optional[str] = None  # <-- поле для кода качества