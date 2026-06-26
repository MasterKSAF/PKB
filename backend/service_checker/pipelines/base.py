#!/usr/bin/env python3
"""
PKB Neuroassistant — Base classes for Pipeline Testing.

Определяет базовые типы и движок выполнения пайплайнов.
"""

from __future__ import annotations

import asyncio
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


def save_parser_result_as(key: str):
    """Вернуть check-функцию, сохраняющую результат парсинга в PipelineContext под указанным ключом.

    Используется для передачи полного ParserResult из шага парсинга
    в шаг конвертации (Converter-Validator требует документ целиком).
    """
    def _save(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return True, "пустой ответ (пропущено)"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return True, "не JSON (пропущено)"
        ctx.set(key, data)
        return True, f"результат сохранён как {key}"
    return _save


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
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Ленивая инициализация HTTP-клиента (SSL certs загружаются только при первом использовании)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                trust_env=False,
            )
        return self._client

    @client.setter
    def client(self, value: httpx.AsyncClient) -> None:
        self._client = value

    async def _ensure_project(self, ctx: PipelineContext, auth_token: Optional[str] = None) -> None:
        """Create or get a project. Raises RuntimeError if impossible."""
        import json as _json
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        base_url = f"http://{self.base_host}:18083/api/v1/chat/projects"

        # 1. Пытаемся создать проект (retry 3 раза), code с timestamp чтобы избежать
        #    UniqueViolation при параллельных или последовательных прогонах
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        for attempt in range(3):
            try:
                project_code = f"PIPELINE_{ts}_{attempt}"
                body = _json.dumps({"code": project_code, "name": "Pipeline Test Project"}).encode()
                resp = await self.client.post(base_url, content=body, headers=headers)
                if resp.status_code == 201:
                    data = resp.json()
                    pid = data.get("project_id") or (data.get("data") or {}).get("id")
                    if pid:
                        ctx.set("project_id", pid)
                        print(f"     ℹ Создан проект project_id={pid}")
                        return
                elif resp.status_code == 409:
                    # Проект уже существует — переходим к GET
                    break
                elif resp.status_code == 500:
                    # Сервис вернул 500 (например UniqueViolation вместо 409) —
                    # пробуем следующий attempt с другим code
                    body_text = (resp.text[:200] if resp.text else "")
                    print(f"     ⚠ Проект не создан (HTTP {resp.status_code}), попытка {attempt+1}/3: {body_text}")
            except Exception as e:
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
                            ctx.set("project_id", pid)
                            print(f"     ℹ Получен проект project_id={pid} из списка")
                            return
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(1)
                continue

        raise RuntimeError("Cannot create or fetch project for chat sessions")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def ping_service(self, port: int, health_paths: Optional[List[str]] = None) -> bool:
        """Проверить, отвечает ли сервис на health-эндпоинты."""
        if health_paths is None:
            health_paths = [
                "/health",
                "/api/v1/health",
                "/api/v1/system/health",
                "/api/v1/",
                "/",
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

        Формат плейсхолдера:
          "{key}" — строка (str(value))
          __INLINE__{key} — inline-значение (dict/list → как JSON, str → как строка)
        """
        if body is None:
            return None

        # Заменяем __INLINE__ маркеры на уникальные ID до json.dumps,
        # чтобы json.dumps не обернул их в кавычки как строки
        _uid = 0
        inline_map: Dict[str, Any] = {}

        def _replace_inline(val: Any) -> Any:
            nonlocal _uid
            if isinstance(val, str) and val.startswith("__INLINE__"):
                key = val[len("__INLINE__"):]
                uid = f"__INLINE_{_uid}__"
                _uid += 1
                inline_map[uid] = key
                return uid
            return val

        # Рекурсивно обходим dict/list
        def _walk(node: Any) -> Any:
            if isinstance(node, dict):
                return {k: _walk(_replace_inline(v)) for k, v in node.items()}
            elif isinstance(node, list):
                return [_walk(_replace_inline(item)) for item in node]
            return node

        processed = _walk(body)
        text = json.dumps(processed)

        # Подставляем контекстные переменные в строковые плейсхолдеры
        for ctx_key, ctx_value in ctx.variables.items():
            # "{key}" → строка
            quoted = '"' + "{" + ctx_key + "}" + '"'
            if quoted in text:
                text = text.replace(quoted, json.dumps(str(ctx_value)))

        # Подставляем inline-значения (снимаем кавычки, которые добавил json.dumps)
        for uid, ctx_key in inline_map.items():
            ctx_value = ctx.variables.get(ctx_key)
            if isinstance(ctx_value, (dict, list)):
                replacement = json.dumps(ctx_value, ensure_ascii=False)
            elif isinstance(ctx_value, bool):
                replacement = "true" if ctx_value else "false"
            elif isinstance(ctx_value, (int, float)):
                replacement = str(ctx_value)
            elif ctx_value is None:
                replacement = "null"
            else:
                replacement = json.dumps(str(ctx_value))
            # json.dumps обернул uid в кавычки: "__INLINE_0__" → убираем
            text = text.replace('"' + uid + '"', replacement)

        return json.loads(text)

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
        # Порт из MODE_PORTS имеет приоритет (единый источник, поддерживает --spd)
        svc_port = self._get_service_port(step.service)
        target_port = svc_port if svc_port is not None else step.port
        url = f"http://{self.base_host}:{target_port}{resolved_path}"
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
                    body_snippet = (resp.text[:200] if resp.text else "")
                    step.error = f"Expected HTTP {step.expected_status}, got {resp.status_code} after {step.retry_max} retries"
                    if body_snippet:
                        step.error += f" | body: {body_snippet}"
                    step.status = StepStatus.FAILED
                    return step
            
            if not status_ok:
                body_snippet = (resp.text[:200] if resp.text else "")
                step.error = f"Expected HTTP {step.expected_status}, got {resp.status_code}"
                if body_snippet:
                    step.error += f" | body: {body_snippet}"
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
                try:
                    check_ok, check_msg = step.check(step.response_body, ctx, actual_status=step.actual_status)
                except TypeError:
                    # Обратная совместимость: check без параметра status
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
        response_body: Optional[str],
        extract_keys: List[str],
        ctx: PipelineContext,
    ) -> None:
        """Извлечь ID из ответа и сохранить в контекст."""
        if not response_body:
            return
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
                    "task_id_2": ["task_id", "taskId"],
                    "draft_id": ["id", "draft_id", "draftId"],
                    "draft_id_2": ["draft_id", "draftId", "id"],
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

        # 2. Pre-prepare: дропнуть FK из старых миграций (совместимость)
        if "rag_builder" in pipeline.services:
            try:
                import subprocess
                r = subprocess.run(
                    ["docker", "exec", "pkb-postgres", "psql", "-U", "pkb", "-d", "pkb_neuro", "-c",
                     "ALTER TABLE IF EXISTS rag.document_chunks DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_section_id;"],
                    capture_output=True, timeout=10,
                )
                if r.returncode == 0:
                    print(f"     ℹ Дропнут FK fk_rag_document_chunks_section_id")
            except Exception:
                pass

        # 3. Pre-prepare: создаём проект для чат-сессий (QS-3)
        if "query" in pipeline.services:
            # Пробуем взять токен из контекста, если auth уже был
            pre_token = str(ctx.get("access_token")) if ctx.has("access_token") else None
            await self._ensure_project(ctx, pre_token)

        # 4. Построение шагов
        try:
            steps = pipeline.build_steps(ctx)
        except Exception as e:
            result.error = f"Ошибка построения шагов: {e}"
            result.passed = False
            return result

        result.steps = steps
        result.total_steps = len(steps)

        # 4. Выполнение шагов
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

        # 5. Итог
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
        """Получить порт сервиса по ключу.

        Использует MODE_PORTS как единый источник истины.
        При --spd порт rag_search меняется через MODE_PORTS глобально.
        """
        from service_checker.services import MODE_PORTS
        return MODE_PORTS.get(service_key)


# ── Вспомогательные проверки для шагов ────────────────────────────────


def check_json_field(
    field_path: str,
    expected_type: type,
    optional: bool = False,
) -> Callable[[Optional[str], PipelineContext], Tuple[bool, str]]:
    """Проверить, что JSON-ответ содержит поле с ожидаемым типом.

    :param field_path: путь к полю (точечная нотация, например data.id)
    :param expected_type: ожидаемый тип (str, dict, list, int, bool)
    :param optional: если True, отсутствие поля не считается ошибкой
    """
    def _check(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return (True, "Пустой ответ (пропущено)") if optional else (False, "Пустой ответ")
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
                return (True, f"Поле '{field_path}' не найдено (пропущено)") if optional else (False, f"Поле '{field_path}' не найдено в ответе")

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

        _alt_map = {
            "draft_id": ["id", "draft_id", "draftId"],
            "document_id": ["id", "document_id", "docId"],
            "version_id": ["id", "version_id", "versionId"],
            "task_id": ["task_id", "taskId"],
            "user_id": ["id", "userId", "user_id"],
        }

        def _deep_search(obj: Any, key: str) -> Optional[Any]:
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                # Проверка альтернативных имён
                for alt in _alt_map.get(key, []):
                    if alt in obj:
                        return obj[alt]
                # Рекурсивный поиск
                for v in obj.values():
                    result = _deep_search(v, key)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = _deep_search(item, key)
                    if result is not None:
                        return result
            return None

        for field_path, expected_type in schema.items():
            parts = field_path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    # Fallback: рекурсивный поиск по всему дереву
                    current = _deep_search(data, field_path)
                    if current is None:
                        return False, f"Поле '{field_path}' не найдено в ответе"
                    break

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


def check_rag_search_results(
    require_sources: bool = False,
) -> Callable[[Optional[str], PipelineContext], Tuple[bool, str]]:
    """Проверить ответ RAG Search по source-индексам (document_id + section_id).

    Валидация по source (document_id + section_id), не по chunk_id.
    chunk_id — технический retrieval ID, не используется для цитирования.

    :param require_sources: если True — хотя бы один результат должен содержать source
    """
    def _check(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        if not body:
            return False, "Пустой ответ"
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return False, f"Невалидный JSON: {e}"

        results = data.get("results", [])
        if not isinstance(results, list):
            return False, f"'results' должен быть списком, получен {type(results).__name__}"

        if not results:
            if require_sources:
                return False, "Нет результатов поиска (требовались source-индексы)"
            return True, "results=[] (нет результатов, валидация по source не требуется)"

        # Валидация по source-индексам (document_id + section_id)
        checked = 0
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                return False, f"results[{i}] не объект: {type(result).__name__}"

            source = result.get("source")
            if not isinstance(source, dict):
                return False, f"results[{i}].source отсутствует или не объект"

            doc_id = source.get("document_id")
            sec_id = source.get("section_id")
            if doc_id is None or sec_id is None:
                return False, f"results[{i}].source: document_id или section_id отсутствуют"

            # Проверка retrieval-метаданных (технические, не用于 цитирования)
            retrieval = result.get("retrieval")
            if retrieval is not None:
                if not isinstance(retrieval, dict):
                    return False, f"results[{i}].retrieval не объект: {type(retrieval).__name__}"
                chunk_id = retrieval.get("chunk_id")
                score = retrieval.get("score")
                mode = retrieval.get("mode")
                if chunk_id is None or score is None or mode is None:
                    return False, f"results[{i}].retrieval: chunk_id/score/mode обязательны"

            checked += 1

        return True, f"results[{checked}/{len(results)}]: валидация по source-индексам (document_id+section_id) пройдена"
    return _check
