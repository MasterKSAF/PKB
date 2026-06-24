"""
Фабрика стандартизаторов для разных схем вывода.
"""
import logging
from typing import Dict, Type
from app.services.standardizer import JsonStandardizer, BaseStandardizer

logger = logging.getLogger(__name__)


class StandardizerFactory:
    """Регистрирует и возвращает стандартизаторы по имени схемы."""

    _registry: Dict[str, Type[BaseStandardizer]] = {
        "raw_ocr_v4": JsonStandardizer,  # базовая схема
        # можно добавить другие: "raw_ocr_v5": V5Standardizer, и т.д.
    }

    @classmethod
    def register(cls, schema_name: str, standardizer_class: Type[BaseStandardizer]):
        """
        Регистрирует новый стандартизатор для указанной схемы.
        """
        cls._registry[schema_name] = standardizer_class
        logger.info("Registered standardizer for schema: %s", schema_name)

    @classmethod
    def get_standardizer(cls, schema_name: str) -> BaseStandardizer:
        """
        Возвращает экземпляр стандартизатора для указанной схемы.
        Если схема не найдена, возвращает стандартизатор по умолчанию.
        """
        standardizer_class = cls._registry.get(schema_name)
        if not standardizer_class:
            logger.warning(
                "Standardizer for schema '%s' not found, using default 'raw_ocr_v4'",
                schema_name,
            )
            standardizer_class = cls._registry["raw_ocr_v4"]
        logger.debug("Returning standardizer for schema: %s", schema_name)
        return standardizer_class()