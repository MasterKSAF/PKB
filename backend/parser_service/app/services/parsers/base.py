"""
Базовый интерфейс для всех парсеров документов.
Определяет единый контракт и структуру результата.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any


@dataclass
class ParseResult:
    """
    Результат работы парсера.
    full_json: полная структура документа в JSON (от opendataloader_pdf)
    images: список кортежей (page_num, image_bytes, extension) для загрузки в MinIO
    total_pages: общее количество страниц
    """
    full_json: Dict[str, Any]
    images: List[Tuple[int, bytes, str]] = field(default_factory=list)
    total_pages: int = 1


class BaseParser(ABC):
    """Абстрактный парсер. Все конкретные парсеры должны наследовать его."""

    @abstractmethod
    async def parse(self, file_bytes: bytes, options: Dict[str, bool]) -> ParseResult:
        """
        Асинхронно парсит файл и возвращает структурированный результат.
        :param file_bytes: содержимое файла в байтах
        :param options: опции парсинга (extract_tables, extract_images и т.д.)
        """
        raise NotImplementedError