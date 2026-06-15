"""
Модуль расширенной безопасности PDF (синхронная версия для вызова в потоке).
Выполняет проверки:
- Расширение файла (.pdf)
- Unicode-маскировка в имени файла
- Опасные ключи PDF (/EmbeddedFile, /JS, /JavaScript, /Launch)
- JBIG2 (опционально)
- YARA-правила (опционально)
- Логирование больших файлов (не блокирует)
"""

import logging
import os
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Попытка импорта YARA (опционально)
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    logger.warning("YARA module not installed. Security scanning disabled.")


class SecurityScanner:
    """Статический класс для синхронной проверки безопасности PDF."""

    # Опасные ключи, которые всегда блокируются
    DANGEROUS_KEYS = {b"/EmbeddedFile", b"/JS", b"/JavaScript", b"/Launch"}

    @classmethod
    def scan_pdf(
        cls,
        file_bytes: bytes,
        original_filename: str,
        yara_rules_path: str,
        max_font_stream: int,
        reject_jbig2: bool,
        enable_yara: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Синхронная проверка безопасности.

        Args:
            file_bytes: Содержимое PDF.
            original_filename: Имя файла.
            yara_rules_path: Путь к директории с YARA-правилами.
            max_font_stream: Максимальный размер шрифтового потока (для лога).
            reject_jbig2: Отклонять ли JBIG2Decode.
            enable_yara: Включено ли YARA-сканирование.

        Returns:
            (is_safe, error_message)
        """
        logger.debug("Security scan started for %s", original_filename)
        try:
            # 1. Проверка расширения
            if not cls._check_extension(original_filename):
                return False, f"File extension not allowed: {original_filename}"

            # 2. Unicode-маскировка
            if not cls._check_unicode_safety(original_filename):
                return False, "Filename contains suspicious Unicode control characters"

            # 3. JBIG2 – блокируем только если явно включено
            if b"/JBIG2Decode" in file_bytes:
                if reject_jbig2:
                    return False, "JBIG2Decode filter detected (rejected by configuration)"
                else:
                    logger.warning("JBIG2Decode filter detected in %s (not rejected)", original_filename)

            # 4. Опасные ключи (всегда блокируем)
            for key in cls.DANGEROUS_KEYS:
                if key in file_bytes:
                    return False, f"Suspicious PDF key found: {key.decode('ascii', errors='ignore')}"

            # 5. YARA (опционально)
            if enable_yara and YARA_AVAILABLE:
                yara_result = cls._yara_scan_sync(file_bytes, yara_rules_path)
                if not yara_result[0]:
                    return False, yara_result[1]

            # 6. Большие файлы – только лог, НЕ БЛОКИРУЕМ
            if len(file_bytes) > max_font_stream:
                logger.warning("Large PDF file: %d bytes (exceeds %d), but accepted", len(file_bytes), max_font_stream)

            return True, None
        except Exception as e:
            logger.error("Security scan exception: %s", e, exc_info=True)
            return False, f"Security scan internal error: {str(e)}"
        finally:
            logger.debug("Security scan finished for %s", original_filename)

    @staticmethod
    def _check_extension(filename: str) -> bool:
        """Проверяет, что расширение файла .pdf."""
        return filename.lower().endswith('.pdf')

    @staticmethod
    def _check_unicode_safety(filename: str) -> bool:
        """
        Защита от Unicode-маскировки:
        - RTL override (U+202E)
        - другие опасные управляющие символы
        - скрытое расширение (.pdf.exe)
        """
        dangerous_chars = {'\u202E', '\u202D', '\u200F', '\u200E', '\u2066', '\u2067', '\u2068', '\u2069'}
        if any(c in filename for c in dangerous_chars):
            return False
        # Проверка на .pdf с последующей точкой (маскировка расширения)
        if re.search(r'\.pdf[^.]*\.', filename, re.IGNORECASE):
            return False
        return True

    @staticmethod
    def _yara_scan_sync(data: bytes, rules_path: str) -> Tuple[bool, Optional[str]]:
        """Синхронное YARA-сканирование."""
        if not os.path.isdir(rules_path):
            return True, None
        rules_files = {}
        for fname in os.listdir(rules_path):
            if fname.endswith('.yar'):
                rules_files[fname] = os.path.join(rules_path, fname)
        if not rules_files:
            return True, None
        try:
            compiled = yara.compile(filepaths=rules_files)
            matches = compiled.match(data=data)
            if matches:
                return False, f"YARA rule triggered: {matches[0].rule}"
            return True, None
        except Exception as e:
            logger.error("YARA scan error: %s", e)
            return True, None