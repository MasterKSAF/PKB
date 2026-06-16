"""
Модуль расширенной безопасности PDF (синхронная версия для вызова в потоке).
Выполняет проверки:
- Unicode-маскировка в имени файла
- Опасные ключи PDF (/EmbeddedFile, /JS, /JavaScript, /Launch)
- JBIG2 (опционально)
- YARA-правила (опционально)
- Логирование больших файлов (не блокирует)

Для каждой проверки предусмотрен переключатель блокировки (см. константы ниже).
Если переключатель = True, обнаружение проблемы вызывает ошибку.
Если False, проблема только логируется, но обработка продолжается.
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


# ========== НАСТРОЙКИ БЛОКИРОВКИ ПО КАЖДОЙ ПРОВЕРКЕ ==========
# Если True – проверка является блокирующей (при обнаружении угрозы возвращается ошибка).
# Если False – угроза только логируется, но обработка продолжается.

BLOCK_ON_UNICODE_CHECK = False         # Блокировать при обнаружении Unicode-маскировки
BLOCK_ON_JBIG2_CHECK = False           # Блокировать при обнаружении /JBIG2Decode (если reject_jbig2=True)
BLOCK_ON_DANGEROUS_KEYS = False        # Блокировать при обнаружении опасных ключей (/JS, /Launch и т.д.)
BLOCK_ON_YARA = False                  # Блокировать при срабатывании YARA-правил

# Проверка расширения файла полностью удалена, т.к. file_key не содержит расширения.
# =================================================================


class SecurityScanner:
    """Статический класс для синхронной проверки безопасности PDF."""

    # Опасные ключи, которые всегда проверяются (блокировка управляется BLOCK_ON_DANGEROUS_KEYS)
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
            original_filename: Имя файла (используется для логов и проверки Unicode).
            yara_rules_path: Путь к директории с YARA-правилами.
            max_font_stream: Максимальный размер шрифтового потока (для лога).
            reject_jbig2: Отклонять ли JBIG2Decode (влияет на блокировку только если BLOCK_ON_JBIG2_CHECK=True).
            enable_yara: Включено ли YARA-сканирование.

        Returns:
            (is_safe, error_message) – is_safe=False, если хотя бы одна блокирующая проверка провалилась.
        """
        logger.debug("Security scan started for %s", original_filename)
        errors = []  # Список сообщений о блокирующих ошибках

        try:
            # 1. Проверка Unicode-маскировки
            unicode_ok = cls._check_unicode_safety(original_filename)
            if not unicode_ok:
                msg = "Filename contains suspicious Unicode control characters"
                if BLOCK_ON_UNICODE_CHECK:
                    logger.error("Unicode check FAILED (blocking): %s", msg)
                    errors.append(msg)
                else:
                    logger.warning("Unicode check FAILED (non-blocking): %s", msg)

            # 2. Проверка JBIG2 (если включена в настройках reject_jbig2)
            if b"/JBIG2Decode" in file_bytes:
                if reject_jbig2:
                    msg = "JBIG2Decode filter detected (rejected by configuration)"
                    if BLOCK_ON_JBIG2_CHECK:
                        logger.error("JBIG2 check FAILED (blocking): %s", msg)
                        errors.append(msg)
                    else:
                        logger.warning("JBIG2 check FAILED (non-blocking): %s", msg)
                else:
                    logger.warning("JBIG2Decode filter detected in %s (not rejected)", original_filename)

            # 3. Проверка опасных ключей
            for key in cls.DANGEROUS_KEYS:
                if key in file_bytes:
                    msg = f"Suspicious PDF key found: {key.decode('ascii', errors='ignore')}"
                    if BLOCK_ON_DANGEROUS_KEYS:
                        logger.error("Dangerous key check FAILED (blocking): %s", msg)
                        errors.append(msg)
                    else:
                        logger.warning("Dangerous key check FAILED (non-blocking): %s", msg)
                    break  # Достаточно одного ключа

            # 4. YARA-сканирование (опционально)
            if enable_yara and YARA_AVAILABLE:
                yara_ok, yara_msg = cls._yara_scan_sync(file_bytes, yara_rules_path)
                if not yara_ok:
                    if BLOCK_ON_YARA:
                        logger.error("YARA check FAILED (blocking): %s", yara_msg)
                        errors.append(yara_msg)
                    else:
                        logger.warning("YARA check FAILED (non-blocking): %s", yara_msg)

            # 5. Логирование больших файлов (никогда не блокирует)
            if len(file_bytes) > max_font_stream:
                logger.warning("Large PDF file: %d bytes (exceeds %d), but accepted", len(file_bytes), max_font_stream)

            # Если есть блокирующие ошибки – возвращаем False
            if errors:
                # Возвращаем первое сообщение как основное (можно объединить, но для краткости берем первое)
                return False, errors[0]

            return True, None

        except Exception as e:
            logger.error("Security scan exception: %s", e, exc_info=True)
            # Внутренняя ошибка сканера – считаем блокирующей, чтобы не пропустить потенциально опасный файл
            return False, f"Security scan internal error: {str(e)}"
        finally:
            logger.debug("Security scan finished for %s", original_filename)

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
        """Синхронное YARA-сканирование. Возвращает (ok, сообщение)."""
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
            # При ошибке YARA – не блокируем, только логируем (возвращаем True)
            return True, None