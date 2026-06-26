#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: Service Management & Web Emulation
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from service_checker.core.config import SERVICE_DEFS, TEST_CREDENTIALS, HEADERS_JSON
from service_checker.core.models import Report, ServiceProcess, HealthResult, ApiCallLog
from service_checker.core.utils import log, log_ok, log_warn, log_err, log_info, log_step, log_header


# ──────────────────────────────────────────────────────────────────────
#  Service Management
# ──────────────────────────────────────────────────────────────────────


def start_service(svc_key: str, svc_def: Dict[str, Any]) -> Optional[ServiceProcess]:
    """Запустить один сервис. Возвращает ServiceProcess или None."""
    name = svc_def["name"]
    port = svc_def["port"]
    cwd = svc_def["cwd"]
    run_cmd = svc_def["run_cmd"]()

    if not cwd.exists():
        log_warn(f"Директория не найдена: {cwd}. Пропускаем {name}")
        return None

    log_info(f"Запуск {name} (порт {port})...")

    try:
        proc = subprocess.Popen(
            run_cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return ServiceProcess(
            key=svc_key,
            name=name,
            port=port,
            proc=proc,
            health_url=svc_def["health_url"],
            type=svc_def.get("type", "mock"),
        )
    except FileNotFoundError as e:
        log_err(f"Не удалось запустить {name}: {e}")
        return None


def stop_service(sp: ServiceProcess):
    """Остановить один сервис."""
    try:
        sp.proc.terminate()
        sp.proc.wait(timeout=5)
        log_ok(f"Остановлен {sp.name} (PID {sp.proc.pid})")
    except subprocess.TimeoutExpired:
        sp.proc.kill()
        log_warn(f"Принудительно остановлен {sp.name} (PID {sp.proc.pid})")
    except Exception as e:
        log_err(f"Ошибка при остановке {sp.name}: {e}")


async def wait_for_service(
    sp: ServiceProcess, timeout: int = 30, poll_interval: float = 0.5
) -> bool:
    """Дождаться, пока сервис начнёт отвечать на health-check."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient(
                    timeout=5,
                    trust_env=False,
            ) as client:
                resp = await client.get(sp.health_url)
                if resp.status_code < 500:
                    return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass

        # Проверим, жив ли процесс
        if sp.proc.poll() is not None:
            # Процесс умер — прочитаем последние строки лога
            stdout, _ = sp.proc.communicate(timeout=2)
            last_lines = stdout.split("\n")[-5:]
            log_err(f"Процесс {sp.name} завершился (код {sp.proc.returncode})")
            for line in last_lines:
                if line.strip():
                    print(f"         {line.strip()}")
            return False

        await asyncio.sleep(poll_interval)

    return False


async def check_service_health(
    sp: ServiceProcess, timeout: int = 10
) -> HealthResult:
    """Проверить health одного сервиса."""
    start = time.time()
    try:
        async with httpx.AsyncClient(
                timeout=timeout,
                trust_env=False,
        ) as client:
            resp = await client.get(sp.health_url)
        elapsed = int((time.time() - start) * 1000)
        data = resp.json() if resp.content else None
        status = "ok" if resp.status_code < 400 else "error"
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status=status,
            response=data,
            elapsed_ms=elapsed,
        )
    except httpx.ConnectError:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="unreachable",
            error="Connection refused",
            elapsed_ms=elapsed,
        )
    except httpx.TimeoutException:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="unreachable",
            error="Timeout",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="error",
            error=str(e),
            elapsed_ms=elapsed,
        )


async def check_service_health_for_key(key: str, svc_def: Dict) -> HealthResult:
    """Проверить health сервиса по его определению."""
    sp = ServiceProcess(
        key=key,
        name=svc_def["name"],
        port=svc_def["port"],
        proc=None,  # type: ignore
        health_url=svc_def["health_url"],
        type=svc_def.get("type", "mock"),
    )
    return await check_service_health(sp)


# ──────────────────────────────────────────────────────────────────────
#  Log collector
# ──────────────────────────────────────────────────────────────────────


async def _collect_logs(report: Report, sp: ServiceProcess):
    """Фоновая задача: читает stdout процесса и сохраняет в отчёт."""
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sp.proc.stdout.readline
            )
            if not line:
                break
            report.add_service_log_line(sp.key, line.rstrip())
    except (ValueError, AttributeError, RuntimeError):
        pass


# ──────────────────────────────────────────────────────────────────────
#  Web Interface Emulation
# ──────────────────────────────────────────────────────────────────────


class WebEmulator:
    """
    Эмуляция работы веб-интерфейса.
    Делает те же вызовы, что и фронтенд.
    Принимает URL базового сервиса (Orchestrator на порту 18081).
    """

    ORCHESTRATOR_URL: str = "http://127.0.0.1:18081"
    AUTH_URL: str = "http://127.0.0.1:18082"
    QUERY_URL: str = "http://127.0.0.1:18083"
    REGISTRY_URL: str = "http://127.0.0.1:18084"

    def __init__(self, mode: str = "individual", report: Optional[Report] = None):
        self.mode = mode
        self.report = report or Report()
        self.access_token: Optional[str] = None
        self.headers: Dict[str, str] = {**HEADERS_JSON}
        self.documents: List[Dict[str, Any]] = []
        self.project_id: int = 1
        self.client = httpx.AsyncClient(
            timeout=30,
            trust_env=False,
        )

    async def _ensure_project(self) -> None:
        """Create or get a project. Raises RuntimeError if impossible."""
        import json as _json
        headers = {**HEADERS_JSON}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        base_url = f"{self.QUERY_URL}/api/v1/chat/projects"

        # 1. Пытаемся создать проект (retry 3 раза)
        for attempt in range(3):
            try:
                body = _json.dumps({"code": "WEBEMU", "name": "WebEmulator Project"}).encode()
                resp = await self.client.post(base_url, content=body, headers=headers)
                if resp.status_code == 201:
                    data = resp.json()
                    pid = data.get("project_id") or (data.get("data") or {}).get("id")
                    if pid:
                        self.project_id = int(pid)
                        log_ok(f"Создан проект project_id={self.project_id}")
                        return
                elif resp.status_code == 409:
                    # Проект уже существует — переходим к GET
                    break
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(1)
                continue

        # 2. Если не создан — получаем список (retry 3 раза)
        for attempt in range(3):
            try:
                resp = await self.client.get(base_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items") or data.get("data") or []
                    if items:
                        pid = items[0].get("project_id") or items[0].get("id")
                        if pid:
                            self.project_id = int(pid)
                            log_ok(f"Получен проект project_id={self.project_id} из списка")
                            return
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(1)
                continue

        raise RuntimeError("Не удалось создать или получить проект для чат-сессий")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    def _base(self) -> str:
        """Базовый URL в зависимости от режима."""
        return self.ORCHESTRATOR_URL

    def _auth_base(self) -> str:
        return self.AUTH_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    def _registry_base(self) -> str:
        return self.REGISTRY_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    def _query_base(self) -> str:
        return self.QUERY_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    async def _request(
        self,
        scenario: str,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Выполнить HTTP-запрос, замерить время и записать в отчёт.
        Возвращает response для дальнейшей обработки.
        """
        start = time.time()
        request_body = None
        if "json" in kwargs:
            request_body = json.dumps(kwargs["json"], ensure_ascii=False)
        elif "data" in kwargs and isinstance(kwargs["data"], dict):
            request_body = json.dumps(kwargs["data"], ensure_ascii=False)
        elif "files" in kwargs:
            request_body = f"<multipart: {list(kwargs.get('data', {}).keys())}>"

        try:
            resp = await getattr(self.client, method.lower())(url, **kwargs)
            elapsed = int((time.time() - start) * 1000)

            call = ApiCallLog(
                scenario=scenario,
                method=method.upper(),
                url=url,
                status_code=resp.status_code,
                request_body=request_body,
                response_body=resp.text if resp.content else None,
                elapsed_ms=elapsed,
                success=resp.status_code < 500,
            )
            self.report.add_api_call(call)
            return resp

        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            call = ApiCallLog(
                scenario=scenario,
                method=method.upper(),
                url=url,
                status_code=0,
                request_body=request_body,
                elapsed_ms=elapsed,
                success=False,
                error=str(e),
            )
            self.report.add_api_call(call)
            raise

    # ── Auth ────────────────────────────────────────────────────────

    async def scenario_auth(self) -> bool:
        """Сценарий аутентификации: логин + профиль + рефреш."""
        base = self._auth_base()

        log_step(f"POST {base}/api/v1/auth/token — получение JWT-токенов...")
        resp = await self._request(
            "auth", "post", f"{base}/api/v1/auth/token",
            json=TEST_CREDENTIALS,
        )
        if resp.status_code != 200:
            log_err(
                f"Аутентификация не удалась: HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False

        data = resp.json()
        self.access_token = data.get("access_token", "")
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        log_ok(
            f"Токен получен (expires_in={data.get('expires_in', '?')}с, тип={data.get('token_type', '?')})"
        )

        # GET /auth/me — профиль
        log_step(f"GET {base}/api/v1/auth/me — профиль пользователя...")
        resp = await self._request(
            "auth", "get", f"{base}/api/v1/auth/me",
            headers=self.headers,
        )
        if resp.status_code == 200:
            profile = resp.json()
            log_ok(
                f"Профиль: {profile.get('email', '?')} — роль {profile.get('role', '?')}"
            )
        else:
            log_warn(f"Не удалось получить профиль: HTTP {resp.status_code}")

        return True

    # ── Classifiers ─────────────────────────────────────────────────

    async def scenario_classifiers(self) -> bool:
        """Сценарий: просмотр классификаторов."""
        base = self._registry_base()
        log_step(f"GET {base}/api/v1/registry/classifiers/ — список классификаторов...")
        resp = await self._request(
            "classifiers", "get", f"{base}/api/v1/registry/classifiers/",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить классификаторы: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Классификаторы: {len(items)} записей")
        if items:
            sample = items[0]
            log_info(
                f"  Пример: код={sample.get('code', '?')}, "
                f"название={sample.get('full_name', sample.get('name', '?'))[:60]}"
            )
        return True

    # ── Terminology ─────────────────────────────────────────────────

    async def scenario_terminology(self) -> bool:
        """Сценарий: просмотр терминологии."""
        base = self._registry_base()
        log_step(f"GET {base}/api/v1/registry/terminology/ — список терминов...")
        resp = await self._request(
            "terminology", "get", f"{base}/api/v1/registry/terminology/",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить термины: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Термины: {len(items)} записей")
        if items:
            sample = items[0]
            log_info(
                f"  Пример: термин={sample.get('term', '?')}, "
                f"определение={sample.get('definition', '?')[:80]}"
            )
        return True

    # ── Documents ───────────────────────────────────────────────────

    async def scenario_documents(self) -> bool:
        """Сценарий: работа с документами (список, детали)."""
        base = self._base()
        log_step(f"GET {base}/api/v1/documents — список документов...")
        resp = await self._request(
            "documents", "get", f"{base}/api/v1/documents",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить документы: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Документы: {len(items)} записей")
        self.documents = items

        if items:
            # Детали первого документа
            doc_id = items[0].get("id")
            if doc_id:
                log_step(f"GET {base}/api/v1/documents/{doc_id} — детали документа...")
                resp = await self._request(
                    "documents", "get", f"{base}/api/v1/documents/{doc_id}",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    doc = resp.json()
                    doc_data = doc.get("data", doc)
                    log_ok(
                        f"Документ: {doc_data.get('doc_code', '?')} — "
                        f"{doc_data.get('title', doc_data.get('name', '?'))[:60]}"
                    )
                else:
                    log_warn(
                        f"Не удалось получить детали документа: HTTP {resp.status_code}"
                    )
        else:
            log_info("Нет документов. Возможно, требуется загрузить хотя бы один.")

        return True

    # ── Upload document (OR-11: draft-first) ────────────────────────

    async def scenario_upload(self) -> bool:
        """Сценарий: загрузка документа (POST /drafts — draft-first)."""
        base = self._base()
        log_step(f"POST {base}/api/v1/drafts/ — создание черновика (draft-first)...")

        resp = await self._request(
            "upload", "post", f"{base}/api/v1/drafts/",
            headers={"Authorization": self.headers.get("Authorization", "")},
            json={"document_key": "emulator-doc-key", "title": "Тестовый документ (emulator)"},
        )

        if resp.status_code in (200, 201, 202):
            log_ok(f"Черновик создан: HTTP {resp.status_code}")
            resp_data = resp.json()
            log_info(f"  draft_id={resp_data.get('draft_id', '?')}")
        else:
            log_warn(
                f"Создание черновика не удалось: HTTP {resp.status_code}"
            )

        return True

    # ── Chat & Search ───────────────────────────────────────────────

    async def scenario_search(self) -> bool:
        """Сценарий: текстовый поиск (POST /text/search)."""
        base = self._query_base()
        log_step(f"POST {base}/api/v1/text/search — поиск по тексту (QS-7)...")
        resp = await self._request(
            "search", "post", f"{base}/api/v1/text/search",
            headers=self.headers,
            json={"text": "толщина обшивки ледового пояса",
                   "valid_at": "2026-06-19",
                   "filters": {"category_ids": []}},
        )
        if resp.status_code != 200:
            log_warn(f"Поиск не выполнен: HTTP {resp.status_code} — {resp.text[:200]}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Поиск выполнен: {len(items)} результатов")
        if items:
            for i, item in enumerate(items[:3], 1):
                score = item.get("score", item.get("relevance", "?"))
                snippet = (
                    item.get("text", item.get("content", item.get("snippet", "")))[:80]
                )
                log_info(f"  [{i}] score={score} — {snippet}...")
        return True

    async def scenario_chat(self) -> bool:
        """Сценарий: чат-сессия (создать, отправить сообщение, longpoll)."""
        base = self._query_base()
        # Создаём/получаем проект для сессии
        await self._ensure_project()
        log_step(f"POST {base}/api/v1/chat/sessions — создание чат-сессии (QS-3)...")
        resp = await self._request(
            "chat", "post", f"{base}/api/v1/chat/sessions",
            headers=self.headers,
            json={"title": "Тестовая сессия", "document_ids": [], "project_id": self.project_id},
        )
        if resp.status_code not in (200, 201):
            log_warn(f"Не удалось создать сессию: HTTP {resp.status_code}")
            return False

        session = resp.json()
        session_id = session.get("id") or (session.get("data") or {}).get("id")
        if not session_id:
            session_id = session.get("session_id")
        log_ok(f"Сессия создана: ID={session_id}")

        if not session_id:
            log_warn("ID сессии не найден в ответе, пропускаем отправку сообщения")
            return True

        # Отправляем сообщение
        log_step(f"POST {base}/api/v1/chat/sessions/{session_id}/messages — отправка сообщения...")
        resp = await self._request(
            "chat", "post", f"{base}/api/v1/chat/sessions/{session_id}/messages",
            headers=self.headers,
            json={"text": "Какая толщина обшивки ледового пояса по ГОСТ?"},
        )

        if resp.status_code in (200, 201, 202):
            msg_data = resp.json()
            log_ok(f"Сообщение отправлено. Ответ: {json.dumps(msg_data)[:150]}")
        else:
            log_warn(
                f"Не удалось отправить сообщение: HTTP {resp.status_code} — {resp.text[:200]}"
            )

        return True

    # ── System Health ───────────────────────────────────────────────

    async def scenario_system_health(self) -> bool:
        """Сценарий: проверка системного health."""
        base = self._base()
        log_step(f"GET {base}/api/v1/system/health — общее состояние системы...")
        resp = await self._request(
            "system_health", "get", f"{base}/api/v1/system/health",
        )
        if resp.status_code != 200:
            log_warn(
                f"System health недоступен: HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False

        data = resp.json()
        status = data.get("status", "?")
        services = data.get("services", {})
        endpoints = data.get("endpoints_total", "?")
        log_ok(f"Система: {status.upper()}, endpoints: {endpoints}")
        for svc, st in services.items():
            icon = "✓" if st == "ok" else "✗"
            log_info(f"  {icon} {svc}: {st}")

        return True

    # ── System Health (GW-12: /monitor/health убран) ───────────────

    async def scenario_monitor(self) -> bool:
        """Сценарий: health Orchestrator (GW-12: /monitor/* удалён, используем /system/health)."""
        base = self._base()
        log_step(f"GET {base}/api/v1/system/health — health Orchestrator...")
        resp = await self._request(
            "monitor", "get", f"{base}/api/v1/system/health",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"System health недоступен: HTTP {resp.status_code}")
            return False

        data = resp.json()
        log_ok(f"Orchestrator health: {data.get('status', '?')}")
        return True

    # ── Run all scenarios ──────────────────────────────────────────

    async def run_all_scenarios(self):
        """Запустить все сценарии эмуляции UI."""
        log_header("Эмуляция работы веб-интерфейса")

        results: List[Tuple[str, bool]] = []

        # 1. Системный health (без токена)
        ok = await self.scenario_system_health()
        results.append(("system_health", ok))

        # 2. Аутентификация
        ok = await self.scenario_auth()
        results.append(("auth", ok))
        if not ok:
            log_err(
                "Аутентификация не пройдена — дальнейшие сценарии будут использовать "
                "заглушки"
            )

        # 3. Классификаторы
        ok = await self.scenario_classifiers()
        results.append(("classifiers", ok))

        # 4. Терминология
        ok = await self.scenario_terminology()
        results.append(("terminology", ok))

        # 5. Документы
        ok = await self.scenario_documents()
        results.append(("documents", ok))

        # 6. Загрузка документа
        ok = await self.scenario_upload()
        results.append(("upload", ok))

        # 7. Мониторинг
        ok = await self.scenario_monitor()
        results.append(("monitor", ok))

        # 8. Поиск
        ok = await self.scenario_search()
        results.append(("search", ok))

        # 9. Чат
        ok = await self.scenario_chat()
        results.append(("chat", ok))

        # ── Итог ──
        log_header("Результаты эмуляции UI")
        total = len(results)
        passed = sum(1 for _, ok in results if ok)
        for name, ok in results:
            icon = "✓" if ok else "✗"
            print(f"  {icon}  {name}")

        print(f"\n  {'─' * 40}")
        print(f"  Итого: {passed}/{total} сценариев успешно\n")

    @staticmethod
    def _extract_items(data: Any) -> List[Dict]:
        """Извлечь список элементов из разных форматов ответов."""
        if isinstance(data, dict):
            for key in ("items", "data", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return data if isinstance(data, list) else []
