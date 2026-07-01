"""
PKB Neuroassistant — HAR vs OpenAPI Validator.

Загружает HAR-файл (HTTP Archive format, JSON), загружает OpenAPI-схему сервиса
и валидирует каждый запрос/ответ из HAR против соответствующего эндпоинта в OpenAPI.

Использование:
    validator = HarValidator(openapi_url="http://service:port/openapi.json")
    await validator.load_openapi()
    report = validator.validate_har("path/to/file.har")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from service_checker.core.openapi_loader import OpenApiLoader


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HarValidationError:
    """Одна ошибка валидации."""
    path: str
    method: str
    status_code: Optional[int]
    category: str  # "status_code", "response_body", "request_body", "missing_endpoint", "query_param"
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class HarValidationResult:
    """Результат валидации одного запроса из HAR."""
    path: str
    method: str
    status_code: Optional[int]
    matched_endpoint: Optional[str]  # OpenAPI path template
    passed: bool
    errors: List[HarValidationError] = field(default_factory=list)
    skipped: bool = False  # True если endpoint не найден в OpenAPI


@dataclass
class HarValidationReport:
    """Полный отчёт по валидации HAR-файла."""
    file_path: str
    total_entries: int
    passed: int
    failed: int
    skipped: int
    results: List[HarValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)  # Общие ошибки (не по записям)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and not self.errors


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class HarValidator:
    """Валидатор HAR-записей против OpenAPI-схемы сервиса."""

    # HTTP-методы, которые есть в OpenAPI
    _HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

    def __init__(
        self,
        openapi_url: str,
        timeout: int = 10,
    ):
        self.openapi_url = openapi_url.rstrip("/")
        self._loader = OpenApiLoader(self.openapi_url, timeout=timeout)
        self._loaded = False
        self._load_errors: List[str] = []

    async def load_openapi(self) -> bool:
        """Загрузить OpenAPI-схему. Вернуть True при успехе."""
        success = await self._loader.load()
        if success:
            self._loaded = True
        else:
            self._load_errors = list(self._loader.errors)
        return success

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    def validate_har(self, har_path: str) -> HarValidationReport:
        """Валидировать HAR-файл против загруженной OpenAPI-схемы.

        Args:
            har_path: Путь к HAR-файлу

        Returns:
            HarValidationReport
        """
        if not self._loaded:
            return HarValidationReport(
                file_path=har_path,
                total_entries=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=["OpenAPI схема не загружена. Вызови load_openapi() first."],
            )

        # Загружаем HAR
        try:
            har_data = self._load_har(har_path)
        except Exception as e:
            return HarValidationReport(
                file_path=har_path,
                total_entries=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=[f"Ошибка загрузки HAR: {e}"],
            )

        entries = self._extract_entries(har_data)

        if not entries:
            return HarValidationReport(
                file_path=har_path,
                total_entries=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=["В HAR-файле не найдено записей (entries)."],
            )

        results: List[HarValidationResult] = []
        passed = 0
        failed = 0
        skipped = 0

        for entry in entries:
            result = self._validate_entry(entry)
            results.append(result)
            if result.skipped:
                skipped += 1
            elif result.passed:
                passed += 1
            else:
                failed += 1

        return HarValidationReport(
            file_path=har_path,
            total_entries=len(entries),
            passed=passed,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    def validate_entries(
        self,
        entries: List[Dict[str, Any]],
    ) -> HarValidationReport:
        """Валидировать список записей в формате HAR entry.

        Каждая entry — dict с ключами:
            method, path, query_string, request_body, response_status, response_body, response_body_text
        """
        if not self._loaded:
            return HarValidationReport(
                file_path="<in-memory>",
                total_entries=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=["OpenAPI схема не загружена."],
            )

        results: List[HarValidationResult] = []
        passed = 0
        failed = 0
        skipped = 0

        for entry in entries:
            result = self._validate_simple_entry(entry)
            results.append(result)
            if result.skipped:
                skipped += 1
            elif result.passed:
                passed += 1
            else:
                failed += 1

        return HarValidationReport(
            file_path="<in-memory>",
            total_entries=len(entries),
            passed=passed,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    @staticmethod
    def _load_har(path: str) -> Dict[str, Any]:
        """Загрузить HAR-файл."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _extract_entries(har_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечь записи из HAR-структуры.

        Поддерживает:
        - Стандартный HAR (browser): log.entries[].request / .response
        """
        entries: List[Dict[str, Any]] = []

        # Стандартный HAR
        log = har_data.get("log", {})
        raw_entries = log.get("entries", [])
        for raw in raw_entries:
            entry = _parse_har_entry(raw)
            if entry:
                entries.append(entry)

        return entries

    def _validate_entry(self, entry: Dict[str, Any]) -> HarValidationResult:
        """Валидировать одну HAR-запись (из стандартного HAR)."""
        method = entry.get("method", "").upper()
        path = entry.get("path", "")
        query_string = entry.get("query_string", "")
        request_body = entry.get("request_body")
        response_status = entry.get("response_status")
        response_body = entry.get("response_body")

        return self._validate_simple_entry({
            "method": method,
            "path": path,
            "query_string": query_string,
            "request_body": request_body,
            "response_status": response_status,
            "response_body": response_body,
        })

    def _validate_simple_entry(self, entry: Dict[str, Any]) -> HarValidationResult:
        """Валидировать одну запись (упрощённый формат)."""
        method = entry.get("method", "").upper()
        path = entry.get("path", "")
        query_string = entry.get("query_string", "")
        request_body = entry.get("request_body")
        response_status = entry.get("response_status")
        response_body = entry.get("response_body")

        # Ищем endpoint в OpenAPI
        oapi_ep = self._loader.match_endpoint(path, method)

        errors: List[HarValidationError] = []

        if oapi_ep is None:
            # Endpoint не найден — не можем валидировать, но отмечаем
            return HarValidationResult(
                path=path,
                method=method,
                status_code=response_status,
                matched_endpoint=None,
                passed=False,
                errors=[
                    HarValidationError(
                        path=path,
                        method=method,
                        status_code=response_status,
                        category="missing_endpoint",
                        message=f"Endpoint {method} {path} не найден в OpenAPI схеме",
                    )
                ],
                skipped=True,
            )

        matched_path = f"{oapi_ep.method} {oapi_ep.path}"

        # 1. Валидируем query-параметры
        if query_string:
            har_params = set()
            for param in query_string.split("&"):
                if "=" in param:
                    har_params.add(param.split("=")[0])

            oapi_params = {p.get("name") for p in oapi_ep.parameters if isinstance(p, dict)}
            extra_params = har_params - oapi_params
            for p in sorted(extra_params):
                errors.append(HarValidationError(
                    path=path, method=method, status_code=response_status,
                    category="query_param",
                    message=f"Запрос содержит query-параметр '{p}', отсутствующий в OpenAPI схеме",
                    details={"param": p},
                ))

        # 2. Валидируем status code
        if response_status is not None:
            status_str = str(response_status)
            if status_str not in oapi_ep.responses and "default" not in oapi_ep.responses:
                errors.append(HarValidationError(
                    path=path, method=method, status_code=response_status,
                    category="status_code",
                    message=f"Status code {response_status} не описан в OpenAPI для {method} {oapi_ep.path}. "
                            f"Ожидаемые: {', '.join(sorted(oapi_ep.responses.keys()))}",
                    details={
                        "actual": response_status,
                        "expected": list(oapi_ep.responses.keys()),
                    },
                ))

        # 3. Валидируем response body через JSON Schema
        if response_body is not None and response_status is not None:
            oapi_resp_schema = oapi_ep.responses.get(str(response_status))
            if oapi_resp_schema is None:
                oapi_resp_schema = oapi_ep.responses.get("default")
            if oapi_resp_schema:
                body_errors = self._validate_json_schema(
                    response_body, oapi_resp_schema, f"Response body {method} {path}"
                )
                for err in body_errors:
                    errors.append(HarValidationError(
                        path=path, method=method, status_code=response_status,
                        category="response_body",
                        message=err,
                    ))

        # 4. Валидируем request body через JSON Schema
        if request_body is not None and oapi_ep.request_body:
            body_errors = self._validate_json_schema(
                request_body, oapi_ep.request_body, f"Request body {method} {path}"
            )
            for err in body_errors:
                errors.append(HarValidationError(
                    path=path, method=method, status_code=response_status,
                    category="request_body",
                    message=err,
                ))

        return HarValidationResult(
            path=path,
            method=method,
            status_code=response_status,
            matched_endpoint=matched_path,
            passed=len(errors) == 0,
            errors=errors,
        )

    def _validate_json_schema(
        self,
        instance: Any,
        schema: Dict[str, Any],
        label: str,
    ) -> List[str]:
        """Валидировать JSON-данные против JSON Schema."""
        import jsonschema  # type: ignore[import-untyped]
        errors: List[str] = []
        validator = jsonschema.Draft7Validator(schema)
        validation_errors = list(validator.iter_errors(instance))
        for ve in validation_errors:
            errors.append(f"{label}: {ve.message} (path: {'/'.join(str(p) for p in ve.absolute_path)})")
        return errors


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------


def _parse_har_entry(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Извлечь упрощённую запись из стандартного HAR entry."""
    try:
        request = raw.get("request", {})
        if not request:
            return None
        response = raw.get("response", {})

        method = request.get("method", "").upper()

        # Парсим URL — извлекаем path и query
        url_str = request.get("url", "")
        parsed = urlparse(url_str)
        path = parsed.path
        query_string = parsed.query

        # Request body
        request_body: Optional[Any] = None
        post_data = request.get("postData", {})
        if post_data:
            text = post_data.get("text", "")
            if text:
                try:
                    request_body = json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    request_body = text

        # Response
        response_status = response.get("status")

        # Response body
        response_body: Optional[Any] = None
        content = response.get("content", {})
        resp_text = content.get("text", "")
        if resp_text:
            mime_type = content.get("mimeType", "")
            try:
                if "json" in mime_type:
                    response_body = json.loads(resp_text)
                else:
                    response_body = resp_text
            except (json.JSONDecodeError, TypeError):
                response_body = resp_text

        return {
            "method": method,
            "path": path,
            "query_string": query_string,
            "request_body": request_body,
            "response_status": response_status,
            "response_body": response_body,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Форматирование отчёта
# ---------------------------------------------------------------------------


def format_har_report(report: HarValidationReport) -> str:
    """Форматировать отчёт валидации HAR в читаемый текст."""
    lines: List[str] = []
    w = lines.append

    w(f"\n📋 HAR Validation Report: {os.path.basename(report.file_path)}")
    w(f"   Total entries: {report.total_entries}")
    w(f"   ✅ Passed: {report.passed}")
    w(f"   ❌ Failed: {report.failed}")
    w(f"   ⏭️  Skipped (no OpenAPI match): {report.skipped}")

    if report.errors:
        w(f"\n⚠️  Общие ошибки:")
        for err in report.errors:
            w(f"   - {err}")

    if report.failed > 0 or report.skipped > 0:
        w(f"\n📝 Детализация:")
        for r in report.results:
            if not r.passed or r.skipped:
                status = "⏭️" if r.skipped else "❌"
                w(f"\n  {status} {r.method} {r.path}")
                if r.matched_endpoint:
                    w(f"     Matched: {r.matched_endpoint}")
                if r.status_code:
                    w(f"     Status: {r.status_code}")
                for err in r.errors:
                    w(f"     🔸 [{err.category}] {err.message}")

    return "\n".join(lines)
