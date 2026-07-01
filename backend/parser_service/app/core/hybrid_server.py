"""
Управление гибридным сервером opendataloader-pdf-hybrid.
Запускается как фоновый процесс, проверяется доступность по HTTP.
"""
import subprocess
import time
import logging
import shutil
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class HybridServer:
    """Контроллер для гибридного сервера."""

    def __init__(self, host: str = "localhost", port: int = 5002, startup_timeout: int = 60):
        self.host = host
        self.port = port
        self.startup_timeout = startup_timeout
        self._process: Optional[subprocess.Popen] = None
        self._started = False
        self._executable = self._find_executable()

    def _find_executable(self) -> Optional[str]:
        """Ищет исполняемый файл opendataloader-pdf-hybrid."""
        # Проверяем в PATH
        exe = shutil.which("opendataloader-pdf-hybrid")
        if exe:
            return exe
        # Проверяем в виртуальном окружении
        venv_bin = os.path.join(sys.prefix, "bin", "opendataloader-pdf-hybrid")
        if os.path.exists(venv_bin):
            return venv_bin
        # Проверяем в site-packages (редко)
        return None

    def start(self) -> bool:
        """
        Запускает гибридный сервер в фоновом режиме.
        Возвращает True, если сервер успешно запущен и доступен.
        """
        if self._started:
            logger.debug("Hybrid server already started")
            return True

        if not self._executable:
            logger.error("opendataloader-pdf-hybrid not found. Install: pip install opendataloader-pdf[hybrid]")
            return False

        logger.info("Starting hybrid server on %s:%d using %s", self.host, self.port, self._executable)
        try:
            # Запускаем процесс с перенаправлением вывода для отладки
            self._process = subprocess.Popen(
                [
                    self._executable,
                    "--host", self.host,
                    "--port", str(self.port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                text=True,
            )
            # Ждём, пока сервер станет доступен
            if self._wait_for_ready():
                self._started = True
                logger.info("Hybrid server started successfully")
                return True
            else:
                # Логируем вывод процесса для диагностики
                stdout, stderr = self._process.communicate(timeout=2)
                if stdout:
                    logger.error("Hybrid server stdout: %s", stdout)
                if stderr:
                    logger.error("Hybrid server stderr: %s", stderr)
                logger.error("Hybrid server did not become ready in %d seconds", self.startup_timeout)
                self.stop()
                return False
        except Exception as e:
            logger.exception("Failed to start hybrid server: %s", e)
            return False

    def _wait_for_ready(self) -> bool:
        """Проверяет доступность сервера через HTTP запрос к /health или /."""
        url = f"http://{self.host}:{self.port}"
        # Пробуем разные пути
        paths = ["/", "/health", "/ping"]
        for attempt in range(self.startup_timeout * 2):  # проверяем каждые 0.5 сек
            for path in paths:
                try:
                    # Используем urllib, чтобы избежать зависимости от requests
                    import urllib.request
                    req = urllib.request.Request(f"{url}{path}", method="GET")
                    with urllib.request.urlopen(req, timeout=1) as resp:
                        if resp.getcode() == 200:
                            return True
                except Exception:
                    pass
            time.sleep(0.5)
        return False

    def stop(self) -> None:
        """Останавливает сервер."""
        if self._process and self._process.poll() is None:
            logger.info("Stopping hybrid server")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        self._process = None
        self._started = False

    def is_running(self) -> bool:
        """Проверяет, запущен ли сервер."""
        if self._process is None:
            return False
        return self._process.poll() is None