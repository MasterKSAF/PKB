"""
Базовый интерфейс для всех парсеров документов.
Определяет единый контракт и структуру результата.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional


@dataclass
class ParseResult:
    """
    Результат работы парсера.

    Attributes:
        full_json: Полный JSON, возвращённый парсером (сырой).
        images: Список кортежей (page_num, file_path, extension) для найденных изображений.
        total_pages: Общее количество страниц в документе.
        temp_dir: Путь к временной директории, созданной парсером (для последующей очистки).
    """
    full_json: Dict[str, Any]
    images: List[Tuple[int, str, str]] = field(default_factory=list)
    total_pages: int = 1
    temp_dir: Optional[str] = None


class BaseParser(ABC):
    """Абстрактный парсер. Все конкретные реализации должны наследовать этот класс."""

    @abstractmethod
    async def parse(
        self,
        file_bytes: bytes,
        options: Dict[str, bool],
        task_id: int,
        total_pages: Optional[int] = None,
    ) -> ParseResult:
        """
        Запускает парсинг документа.

        Args:
            file_bytes: Содержимое файла в байтах.
            options: Словарь опций (extract_tables, extract_images и т.д.).
            task_id: Идентификатор задачи (для логирования).
            total_pages: Предварительно известное количество страниц (опционально).

        Returns:
            ParseResult: Объект с результатами парсинга.
        """
        raise NotImplementedError