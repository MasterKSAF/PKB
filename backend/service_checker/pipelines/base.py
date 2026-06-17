#!/usr/bin/env python3
"""
PKB Neuroassistant — Base classes for Pipeline Testing.

Определяет базовые типы и движок выполнения пайплайнов.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx


# ──────────────────────────────────────────────────────────────
#  S3 / MinIO helpers
# ──────────────────────────────────────────────────────────────


def s3_sign_headers(
    method: str,
    url: str,
    access_key: str,
    secret_key: str,
    body: bytes = b"",
    content_type: str = "application/octet-stream",
    region: str = "us-east-1",
    service: str = "s3",
) -> Dict[str, str]:
    """Вычислить заголовки AWS4-HMAC-SHA256 для S3-запроса."""
    amz_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    date_stamp = amz_date[:8]

    from urllib.parse import urlparse
    parsed = urlparse(url)
    canonical_uri = parsed.path or "/"
    canonical_qs = parsed.query
    host = parsed.hostname or "localhost"
    if parsed.port:
        host = f"{host}:{parsed.port}"

    body_hash = hashlib.sha256(body).hexdigest()

    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{body_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"

    payload_hash = body_hash
    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_qs}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    def _sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = _sign(f"AWS4{secret_key}".encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "Authorization": authorization,
        "X-Amz-Date": amz_date,
        "X-Amz-Content-SHA256": body_hash,
        "Content-Type": content_type,
        "Host": host,
    }


class StepStatus(Enum):
    """Статус выполнения шага пайплайна."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """Определение одного шага пайплайна.

    :param name: Название шага (для отчёта)
    :param service: Ключ сервиса (auth, parser, registry…)
    :param method: HTTP-метод (GET, POST, PUT, PATCH, DELETE)
    :param path: Путь эндпоинта (например /api/v1/parser/process)
    :param port: Порт сервиса
    :param body: Тело запроса как JSON (опционально)
    :param form_body: Тело запроса как form-data (опционально, заменяет body)
    :param content: Бинарное содержимое (опционально, заменяет body/form_body)
    :param params: Query-параметры (опционально)
    :param expected_status: Ожидаемый HTTP-статус (int или set[int])
    :param retry_on: Статусы для автоматического повтора (напр. {409})
    :param retry_delay: Секунд между повторами
    :param retry_max: Максимум повторов
    :param check: Функция проверки ответа (response_body, context) -> (ok, message)
    :param extract_keys: Ключи для извлечения из ответа в контекст
    :param needs_auth: Нужен ли Bearer-токен
    :param extra_headers: Дополнительные HTTP-заголовки (для S3-подписи и т.п.)
    :param skip_if: Функция-условие пропуска шага (context -> bool).
                    Если вернёт True, шаг пропускается (SKIPPED).
                    Используется для ветвлений: один из двух шагов выполняется,
                    второй пропускается.
    :param on_error: Функция, вызываемая при несовпадении HTTP-статуса.
                     Получает (response_body, context) и может сохранить
                     информацию об ошибке в контексте для ветвления.
                     Вызывается ДО возврата FAILED.
    """

    name: str
    service: str
    method: str
    path: str
    port: int
    body: Optional[Dict[str, Any]] = None
    form_body: Optional[Dict[str, Any]] = None
    form_files: Optional[Dict[str, tuple[str, bytes, str]]] = None  # {field: (filename, content, content_type)}
    content: Optional[bytes] = None
    params: Optional[Dict[str, Any]] = None
    expected_status: int | set[int] = 200
    retry_on: Optional[set[int]] = None
    retry_delay: float = 3.0
    retry_max: int = 10
    check: Optional[Callable[[Optional[str], PipelineContext], Tuple[bool, str]]] = None
    extract_keys: Optional[List[str]] = None
    needs_auth: bool = False
    extra_headers: Optional[Dict[str, str]] = None
    skip_if: Optional[Callable[[PipelineContext], bool]] = None
    on_error: Optional[Callable[[Optional[str], PipelineContext], None]] = None

    # Заполняется во время выполнения
    actual_status: int = 0
    elapsed_ms: int = 0
    response_body: Optional[str] = None
    error: Optional[str] = None
    message: str = ""  # Сообщение от check-функции (даже при успехе)
    status: StepStatus = StepStatus.PENDING


@dataclass
class PipelineContext:
    """Контекст выполнения пайплайна.

    Хранит извлечённые ID, токены и прочие переменные между шагами.
    """

    variables: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def has(self, key: str) -> bool:
        return key in self.variables


@dataclass
class PipelineResult:
    """Результат выполнения одного пайплайна."""

    name: str
    description: str
    steps: List[PipelineStep] = field(default_factory=list)
    context: PipelineContext = field(default_factory=PipelineContext)
    passed: bool = False
    ping_ok: bool = False
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    error: Optional[str] = None

    @property
    def api_calls_total(self) -> int:
        return self.total_steps

    @property
    def api_calls_ok(self) -> int:
        return self.passed_steps


class PipelineDef:
    """Базовый класс для определения пайплайна.

    Дочерние классы переопределяют:
    - name — имя пайплайна
    - description — описание
    - build_steps() — построение списка шагов
    """

    name: str = ""
    description: str = ""
    services: List[str] = []  # Какие сервисы участвуют

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить список шагов пайплайна с учётом контекста."""
        raise NotImplementedError


class PipelineRunner:
    """
    Движок выполнения пайплайна.
    Последовательно выполняет шаги, собирает результаты.
    """

    def __init__(
        self,
        base_host: str = "127.0.0.1",
        timeout: int = 30,
    ):
        self.base_host = base_host
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()

    async def ping_service(self, port: int, health_paths: Optional[List[str]] = None) -> bool:
        """Проверить, отвечает ли сервис на health-эндпоинты."""
        if health_paths is None:
            health_paths = [
                "/api/v1/health",
                "/api/v1/system/health",
                "/api/v1/monitor/health",
            ]
        for path in health_paths:
            try:
                resp = await self.client.get(
                    f"http://{self.base_host}:{port}{path}",
                    timeout=2,
                )
                if resp.status_code < 500:
                    return True
            except Exception:
                continue
        return False

    def _resolve_path(self, path: str, ctx: PipelineContext) -> str:
        """Подставить контекстные переменные в путь.

        Формат плейсхолдера: {key}
        """
        resolved = path
        for key, value in ctx.variables.items():
            resolved = resolved.replace(f"{{{key}}}", str(value))
        return resolved

    def _resolve_body(self, body: Optional[Dict], ctx: PipelineContext) -> Optional[Dict]:
        """Подставить контекстные переменные в тело.

        Формат плейсхолдера: {key} (в значениях JSON).
        """
        if body is None:
            return None
        resolved = json.dumps(body)
        for key, value in ctx.variables.items():
            resolved = resolved.replace(f"{{{key}}}", str(value))
        return json.loads(resolved)

    async def run_step(
        self,
        step: PipelineStep,
        ctx: PipelineContext,
        auth_token: Optional[str] = None,
    ) -> PipelineStep:
        """Выполнить один шаг пайплайна."""
        step.status = StepStatus.RUNNING
        start = time.time()

        # Подстановка переменных
        resolved_path = self._resolve_path(step.path, ctx)
        url = f"http://{self.base_host}:{step.port}{resolved_path}"
        body = self._resolve_body(step.body, ctx)

        # Заголовки
        headers = {"Accept": "application/json"}
        if step.needs_auth and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        if step.extra_headers:
            headers.update(step.extra_headers)

        # Выполнение запроса
        try:
            kwargs: Dict[str, Any] = {"headers": headers}
            if step.content is not None:
                kwargs["content"] = step.content
                headers.setdefault("Content-Type", "application/octet-stream")
            elif step.form_body is not None:
                if step.form_files:
                    kwargs["data"] = step.form_body
                    kwargs["files"] = step.form_files
                    # httpx сам выставит multipart/form-data с файлами
                else:
                    kwargs["data"] = step.form_body
                    # httpx автоматически выставит Content-Type: multipart/form-data
            elif body is not None:
                kwargs["json"] = body
                headers.setdefault("Content-Type", "application/json")
            if step.params:
                kwargs["params"] = step.params

            resp = await getattr(self.client, step.method.lower())(url, **kwargs)
            step.elapsed_ms = int((time.time() - start) * 1000)
            step.actual_status = resp.status_code
            step.response_body = resp.text if resp.content else None

            # Проверка статуса (int или set[int])
            if isinstance(step.expected_status, set):
                status_ok = resp.status_code in step.expected_status
            else:
                status_ok = resp.status_code == step.expected_status
            
            # Retry если статус в retry_on
            if not status_ok and step.retry_on and resp.status_code in step.retry_on:
                import asyncio
                for attempt in range(step.retry_max):
                    await asyncio.sleep(step.retry_delay)
                    resp = await getattr(self.client, step.method.lower())(url, **kwargs)
                    step.elapsed_ms = int((time.time() - start) * 1000)
                    step.actual_status = resp.status_code
                    step.response_body = resp.text if resp.content else None
                    if isinstance(step.expected_status, set):
                        status_ok = resp.status_code in step.expected_status
                    else:
                        status_ok = resp.status_code == step.expected_status
                    if status_ok:
                        break
                else:
                    step.error = f"Expected HTTP {step.expected_status}, got {resp.status_code} after {step.retry_max} retries"
                    step.status = StepStatus.FAILED
                    return step
            
            if not status_ok:
                step.error = f"Expected HTTP {step.expected_status}, got {resp.status_code}"
                step.status = StepStatus.FAILED
                # on_error: сохраняем информацию об ошибке для ветвления
                if step.on_error:
                    step.on_error(step.response_body, ctx)
                return step

            # Извлечение контекста
            if step.extract_keys and step.response_body:
                self._extract_context(step.response_body, step.extract_keys, ctx)

            # Пользовательская проверка
            if step.check:
                check_ok, check_msg = step.check(step.response_body, ctx)
                step.message = check_msg or ""  # Сохраняем сообщение даже при успехе
                if not check_ok:
                    step.error = check_msg
                    step.status = StepStatus.FAILED
                    return step

            step.status = StepStatus.PASSED

        except httpx.ConnectError as e:
            step.elapsed_ms = int((time.time() - start) * 1000)
            step.error = f"ConnectError: {e}"
            step.status = StepStatus.FAILED
        except httpx.TimeoutException as e:
            step.elapsed_ms = int((time.time() - start) * 1000)
            step.error = f"Timeout: {e}"
            step.status = StepStatus.FAILED
        except Exception as e:
            step.elapsed_ms = int((time.time() - start) * 1000)
            step.error = str(e)
            step.status = StepStatus.FAILED

        return step

    def _extract_context(
        self,
        response_body: str,
        extract_keys: List[str],
        ctx: PipelineContext,
    ) -> None:
        """Извлечь ID из ответа и сохранить в контекст."""
        try:
            raw = json.loads(response_body)
        except json.JSONDecodeError:
            return

        def _get_by_path(obj: Any, path: str) -> Optional[Any]:
            parts = path.split(".")
            current = obj
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        def _search(obj: Any, key: str) -> Optional[Any]:
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for v in obj.values():
                    result = _search(v, key)
                    if result is not None:
                        return result
                alt_map = {
                    "session_id": ["id", "sessionId", "session_id"],
                    "doc_id": ["id", "document_id", "docId"],
                    "user_id": ["id", "userId", "user_id"],
                    "classifier_code": ["code", "classifier_code"],
                    "term_id": ["id", "term_id", "termId"],
                    "message_id": ["id", "messageId", "message_id"],
                    "task_id": ["task_id", "taskId"],
                    "file_key": ["file_key", "fileKey", "key"],
                    "access_token": ["access_token"],
                    "refresh_token": ["refresh_token"],
                    "pending_id": ["id"],
                    "pending_id2": ["id"],
                    "quar_doc_id": ["id", "document_id"],
                    "quar_doc_id2": ["id", "document_id"],
                    "doc_id_1": ["id", "document_id"],
                    "doc_id_2": ["id", "document_id"],
                }
                for alt in alt_map.get(key, []):
                    if alt in obj:
                        return obj[alt]
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item, key)
                    if result is not None:
                        return result
            return None

        for key in extract_keys:
            if key not in ctx.variables:
                value = _get_by_path(raw, f"data.{key}")
                if value is None:
                    value = _search(raw, key)
                if value is not None:
                    ctx.set(key, value)

    async def run(
        self,
        pipeline: PipelineDef,
        skip_ping: bool = False,
    ) -> PipelineResult:
        """Выполнить пайплайн от начала до конца."""
        result = PipelineResult(name=pipeline.name, description=pipeline.description)
        ctx = PipelineContext()

        print(f"\n  ── [{pipeline.name}] {pipeline.description} ──")

        # 1. Ping всех сервисов пайплайна
        result.ping_ok = True
        if not skip_ping:
            for svc_key in pipeline.services:
                port = self._get_service_port(svc_key)
                if port:
                    alive = await self.ping_service(port)
                    if not alive:
                        print(f"     ❌ {svc_key}: не отвечает на health check")
                        result.ping_ok = False
                    else:
                        print(f"     ✅ {svc_key}: health check ok")
                else:
                    print(f"     ⚠️  {svc_key}: порт не определён")
        else:
            result.ping_ok = True

        # 2. Построение шагов
        try:
            steps = pipeline.build_steps(ctx)
        except Exception as e:
            result.error = f"Ошибка построения шагов: {e}"
            result.passed = False
            return result

        result.steps = steps
        result.total_steps = len(steps)

        # 3. Выполнение шагов
        auth_token: Optional[str] = None
        for i, step in enumerate(steps):
            # Проверяем, не требует ли шаг токен
            if step.needs_auth and auth_token is None:
                # Пробуем взять токен из контекста (если auth-шаг уже выполнен)
                if ctx.has("access_token"):
                    auth_token = str(ctx.get("access_token"))

            # Ветвление: если условие пропуска вернуло True — пропускаем шаг
            if step.skip_if is not None and step.skip_if(ctx):
                step.status = StepStatus.SKIPPED
                step.message = "Шаг пропущен по условию skip_if"
                result.skipped_steps += 1
                print(f"     ⏭️ [{i+1}/{len(steps)}] {step.name} — пропущен (skip_if)")
                continue

            step = await self.run_step(step, ctx, auth_token)

            # Если это auth-шаг и он успешен — сохраняем токен
            if step.service == "auth" and step.status == StepStatus.PASSED:
                if ctx.has("access_token"):
                    auth_token = str(ctx.get("access_token"))

            # Считаем статистику
            if step.status == StepStatus.PASSED:
                result.passed_steps += 1
            elif step.status == StepStatus.FAILED:
                result.failed_steps += 1
            elif step.status == StepStatus.SKIPPED:
                result.skipped_steps += 1

            # Вывод прогресса
            icon = {StepStatus.PASSED: "✅", StepStatus.FAILED: "❌", StepStatus.SKIPPED: "⏭️"}.get(
                step.status, "⏳"
            )
            detail = step.response_body[:80] if step.response_body else ""
            if step.error:
                detail = step.error
            print(f"     {icon} [{i+1}/{len(steps)}] {step.name} — HTTP {step.actual_status} ({step.elapsed_ms}ms) — {detail}")

        # 4. Итог
        # ⏭️ Skipped — не ошибка (ветвление через skip_if).
        # Пайплайн пройден, если ping ок, нет failed шагов, и есть хоть один шаг.
        result.passed = (
            result.ping_ok
            and result.failed_steps == 0
            and result.total_steps > 0
        )
        result.context = ctx

        status_icon = "✅ Пройден" if result.passed else "❌ Сбой"
        print(f"     Итог: {status_icon} | Ping: {'✅' if result.ping_ok else '❌'} | "
              f"Steps: {result.passed_steps}/{result.total_steps}")

        return result

    def _get_service_port(self, service_key: str) -> Optional[int]:
        """Получить порт сервиса по ключу."""
        ports = {
            "gateway": 8080,
            "orchestrator": 8081,
            "auth": 8082,
            "query": 8083,
            "registry": 8084,
            "converter_validator": 8086,
            "parser": 8087,
            "rag_builder": 8090,
            "rag_search": 8091,
            "minio": 19000,  # MinIO S3 API
            "tei": 18092,  # Hugging Face TEI
        }
        return ports.get(service_key)


# ── Вспомогательные проверки для шагов ────────────────────────────────


def check_json_field(
    field_path: str,
    expected_type: type,
) -> Callable[[Optional[str], PipelineContext], Tuple[bool, str]]:
    """Проверить, что JSON-ответ содержит поле с ожидаемым типом.

    :param field_path: путь к полю (точечная нотация, например data.id)
    :param expected_type: ожидаемый тип (str, dict, list, int, bool)
    """
    def _check(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return False, "Пустой ответ"
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return False, f"Невалидный JSON: {e}"

        parts = field_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False, f"Поле '{field_path}' не найдено в ответе"

        if not isinstance(current, expected_type):
            actual = type(current).__name__
            return False, f"Поле '{field_path}' ожидалось {expected_type.__name__}, получен {actual} = {str(current)[:80]}"

        return True, f"{field_path} = {str(current)[:80]}"
    return _check


def check_json_fields(schema: Dict[str, type]) -> Callable:
    """Проверить несколько полей JSON-ответа по схеме.

    :param schema: {field_path: type} — например {"data.id": str, "data.title": str}
    """
    def _check(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return False, "Пустой ответ"
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return False, f"Невалидный JSON: {e}"

        for field_path, expected_type in schema.items():
            parts = field_path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False, f"Поле '{field_path}' не найдено в ответе"

            if not isinstance(current, expected_type):
                actual = type(current).__name__
                return False, f"Поле '{field_path}' ожидалось {expected_type.__name__}, получен {actual}"

        return True, "Все поля валидны"
    return _check


def check_contains_text(expected_substring: str) -> Callable:
    """Проверить, что тело ответа содержит подстроку."""
    def _check(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return False, "Пустой ответ"
        if expected_substring in body:
            return True, f"Ответ содержит '{expected_substring}'"
        return False, f"Ответ не содержит '{expected_substring}'"
    return _check
