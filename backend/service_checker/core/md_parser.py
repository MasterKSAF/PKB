"""
PKB Neuroassistant — Markdown API Documentation Parser.

Парсит docs/api/*.md и извлекает структурированное описание эндпоинтов:
метод, путь, группа, параметры, тело запроса, схема ответа (из JSON-примеров и таблиц полей).

Выходной формат пригоден для преобразования в OpenAPI 3.0 JSON-схему.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── Data types ──────────────────────────────────────────────────────────

@dataclass
class MdField:
    """Поле из таблицы документации."""
    name: str                         # "data.id" или "classifier_system"
    type_raw: str                     # "string", "int", "boolean", "string[]", "bigint | null"
    required: bool = True             # Из колонки "Обязательность"
    description: str = ""


@dataclass
class MdBody:
    """Тело запроса или ответа."""
    status_code: str                  # "200", "201", "default" или "request"
    description: str = ""
    json_example: Optional[Dict[str, Any]] = None
    fields: List[MdField] = field(default_factory=list)


@dataclass
class MdEndpoint:
    """Распарсенный эндпоинт из документации."""
    method: str                       # GET, POST, PUT, PATCH, DELETE
    path: str                         # /api/v1/registry/classifiers
    group: str                        # classifiers, auth, admin, ...
    title: str                        # "Список (плоский)"
    description: str = ""
    # query-параметры
    query_params: List[MdField] = field(default_factory=list)
    # тело запроса (для POST/PUT/PATCH)
    request_body: Optional[MdBody] = None
    # ответы по статус-кодам
    responses: Dict[str, MdBody] = field(default_factory=dict)
    # коды ошибок
    error_codes: List[Tuple[str, str, str]] = field(default_factory=list)  # (http, code, description)


@dataclass
class MdService:
    """Распарсенный сервис из md-файла."""
    title: str                        # "API Registry Service / Registry (registry-service:18084)"
    name: str                         # "Registry Service"
    key: str                          # "registry"
    port: int                         # 18084
    base_path: str = "/api/v1"
    endpoints: List[MdEndpoint] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)  # предупреждения парсера


# ── Вспомогательные утилиты ──────────────────────────────────────────

# Маппинг типов из md → JSON Schema
TYPE_MAP: Dict[str, str] = {
    "string": "string",
    "str": "string",
    "int": "integer",
    "integer": "integer",
    "bigint": "integer",
    "smallint": "integer",
    "float": "number",
    "double": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "dict": "object",
    "object": "object",
    "list": "array",
    "array": "array",
    "date": "string",
    "datetime": "string",
    "timestamp": "string",
    "uuid": "string",
    "json": "object",
    "jsonb": "object",
    "any": {},
}

# Обязательные/опциональные маркеры в таблицах
REQUIRED_MARKERS = {"да", "yes", "+", "true", "обязательный", "обязательно", "required"}
OPTIONAL_MARKERS = {"нет", "no", "-", "false", "необязательный", "optional", "опционально", "null"}


def _map_type(raw: str) -> str:
    """Привести тип из md к JSON Schema type."""
    raw_clean = raw.strip().lower()
    # Сложные типы: "bigint | null" → "integer"
    raw_clean = raw_clean.split("|")[0].split("(")[0].strip()
    # "string[]", "integer[]", "bigint[]" → "array"
    if raw_clean.endswith("[]"):
        return "array"
    # "string | null", "integer | null"
    raw_clean = raw_clean.replace(" | null", "").replace("|null", "").strip()
    return TYPE_MAP.get(raw_clean, "string")


def _extract_method_path(line: str) -> Optional[Tuple[str, str]]:
    """Извлечь (method, path) из строки вида 'GET /api/v1/...' или 'POST /auth/token'."""
    m = re.match(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\S]*)', line.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def _is_code_block_start(line: str) -> bool:
    return line.strip().startswith("```")


def _is_code_block_end(line: str) -> bool:
    return line.strip() == "```" or line.strip().startswith("```")


def _is_table_row(line: str) -> bool:
    """Является ли строка частью markdown-таблицы."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_table_separator(line: str) -> bool:
    """Табличный разделитель вида |---|---|."""
    return "---" in line and _is_table_row(line)


def _parse_table_row(row: str, columns: List[str]) -> Optional[Dict[str, str]]:
    """Распарсить одну строку таблицы в словарь {column_name: value}."""
    cells = [c.strip().strip("`").strip() for c in row.split("|")[1:-1]]
    if len(cells) < len(columns):
        return None
    return dict(zip(columns, cells))


def _detect_table_columns(header: str) -> List[str]:
    """Определить колонки таблицы по заголовку."""
    cells = [c.strip().lower().strip("`").strip() for c in header.split("|")[1:-1]]
    return cells


def _has_required_column(columns: List[str]) -> bool:
    """Есть ли в таблице колонка 'обязательность' или 'обязательный'."""
    for col in columns:
        if col in ("обязательность", "обязательный", "required", "обяз."):
            return True
    return False


def _get_description_between(
    lines: List[str], start: int, end: int
) -> str:
    """Собрать текст между start и end (без заголовков и код-блоков)."""
    parts = []
    in_code = False
    for i in range(start, min(end, len(lines))):
        stripped = lines[i].strip()
        if _is_code_block_start(stripped):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("#") or stripped.startswith("```"):
            continue
        if stripped and not _is_table_row(stripped):
            parts.append(stripped)
    return " ".join(parts).strip()


def _extract_json_from_code_block(lines: List[str], start: int) -> Tuple[Optional[Dict[str, Any]], int]:
    """Извлечь JSON из ```json ... ``` блока, начиная с start (где ```json).
    Возвращает (json_dict, index_after_block).
    """
    if start >= len(lines):
        return None, start
    start_line = lines[start].strip()
    if not start_line.lower().startswith("```json") and not start_line.startswith("```"):
        return None, start

    # Парсим до закрывающего ```
    json_lines: List[str] = []
    i = start + 1
    in_block = True
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "```" or stripped.startswith("```"):
            in_block = False
            i += 1
            break
        json_lines.append(lines[i])
        i += 1

    if in_block:
        return None, i

    json_text = "\n".join(json_lines).strip()
    if not json_text:
        return None, i

    try:
        return json.loads(json_text), i
    except json.JSONDecodeError:
        return None, i


def _extract_field_name_parts(name: str) -> List[str]:
    """Разбить точечное имя поля на части: 'data.items.id' → ['data', 'items', 'id']."""
    return name.strip().split(".")


def _build_schema_from_example(
    example: Dict[str, Any], prefix: str = "", required: bool = True
) -> Dict[str, Any]:
    """Построить JSON Schema из JSON-примера рекурсивно.

    Возвращает Dict в формате JSON Schema:
    {"type": "object", "properties": {...}, "required": [...]}
    """
    if example is None:
        return {}

    if isinstance(example, bool):
        return {"type": "boolean"}

    if isinstance(example, int):
        return {"type": "integer"}

    if isinstance(example, float):
        return {"type": "number"}

    if isinstance(example, str):
        # Простая эвристика: длинные строки → "string", но могут быть date/datetime
        return {"type": "string"}

    if isinstance(example, list):
        items_schema: Dict[str, Any] = {"type": "object"}
        if example:
            # Базовый тип по первому элементу
            items_schema = _build_schema_from_example(example[0])
        return {"type": "array", "items": items_schema}

    if isinstance(example, dict):
        properties: Dict[str, Any] = {}
        required_list: List[str] = []
        for key, value in example.items():
            properties[key] = _build_schema_from_example(value)
            if value is not None:
                required_list.append(key)
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required_list:
            schema["required"] = required_list
        return schema

    return {"type": "string"}


def _merge_schema_with_fields(
    schema: Dict[str, Any],
    fields: List[MdField],
    path: str = "",
) -> Dict[str, Any]:
    """Обогатить JSON Schema информацией из таблицы полей (required, типы, описания)."""
    if not fields:
        return schema

    # Группируем поля по корневому ключу
    root_fields: Dict[str, List[MdField]] = {}
    flat_fields: List[MdField] = []

    for f in fields:
        parts = _extract_field_name_parts(f.name)
        if len(parts) == 1:
            flat_fields.append(f)
        else:
            root_key = parts[0]
            # Сохраняем вложенное поле как есть, но с обрезанным префиксом
            nested = MdField(
                name=".".join(parts[1:]),
                type_raw=f.type_raw,
                required=f.required,
                description=f.description,
            )
            root_fields.setdefault(root_key, []).append(nested)

    schema_type = schema.get("type", "object")
    if schema_type == "object":
        properties = schema.get("properties", {})

        # Плоские поля — добавляем/обновляем
        for f in flat_fields:
            mapped_type = _map_type(f.type_raw)
            prop: Dict[str, Any] = {"type": mapped_type}
            # Уточняем тип для массивов
            if mapped_type == "array" and "[]" in f.type_raw:
                inner = f.type_raw.replace("[]", "").strip()
                prop["items"] = {"type": _map_type(inner)}
            if f.description:
                prop["description"] = f.description
            properties[f.name] = prop

        # Вложенные поля — добавляем рекурсивно в соответствующее свойство
        for root_key, nested_fields in root_fields.items():
            if root_key in properties:
                properties[root_key] = _merge_schema_with_fields(
                    properties[root_key], nested_fields, f"{path}.{root_key}"
                )

        # Обновляем required из таблицы полей
        required_list = schema.get("required", [])
        for f in flat_fields:
            if f.required and f.name not in required_list:
                required_list.append(f.name)
        if required_list:
            schema["required"] = required_list

        schema["properties"] = properties

    return schema




# Заголовки ###, которые не являются эндпоинтами (секции документации)
_NON_ENDPOINT_HEADERS = {
    "группы", "формат ответа", "коды ошибок", "содержание",
    "идентификаторы", "хранение", "передача", "жизненный цикл",
    "модели данных", "примечания", "формат ответа и ошибок",
    "общие положения", "порты сервисов", "мониторинг",
    "сценарий работы", "именование полей", "механизм",
    "иерархия маршрутов",
}

def _is_endpoint_header(text: str) -> bool:
    """Проверить, является ли заголовок ### заголовком эндпоинта."""
    # Содержит HTTP метод
    if re.match(r'(GET|POST|PUT|PATCH|DELETE)\s+/', text):
        return True
    # Нумерованный эндпоинт: "1.1.", "3.2.1." и т.д.
    if re.match(r'^\d+(\.\d+)+\.?\s+', text):
        return True
    # Известный не-эндпоинт
    if text.strip().lower().strip("*") in _NON_ENDPOINT_HEADERS:
        return False
    # Под-нумерация: "2." → может быть эндпоинтом или подразделом
    # Определяем по контексту позже
    return False


# ── Парсер ─────────────────────────────────────────────────────────────

class MdApiParser:
    """Парсер docs/api/*.md файлов."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines: List[str] = []
        self.service: Optional[MdService] = None

    def parse(self) -> MdService:
        """Главный метод: распарсить файл и вернуть MdService."""
        filepath = Path(self.file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        self.lines = filepath.read_text(encoding="utf-8").split("\n")

        self.service = MdService(
            title=filepath.stem,
            name=filepath.stem,
            key=filepath.stem.replace("_service_api", "").replace("_api", ""),
            port=0,
        )

        self._parse_service_header()
        self._parse_endpoints()

        return self.service

    def _parse_service_header(self) -> None:
        """Извлечь название сервиса и порт из первого заголовка."""
        for line in self.lines[:20]:
            # "## API Registry Service / Registry (registry-service:18084)"
            m = re.match(r'^##\s+API\s+(.+?)\s*\([^:]*:(\d+)\)', line)
            if m:
                self.service.title = m.group(1).strip()
                self.service.port = int(m.group(2))
                # key из заголовка: registry-service → registry
                key_match = re.search(r'\((\w+)-service', line)
                if key_match:
                    self.service.key = key_match.group(1)
                # name: "Registry Service" если найдено
                name_match = re.search(r'/\s*(.+?)\s*\(', line)
                if name_match:
                    self.service.name = name_match.group(1).strip()
                return

        # Fallback: ищем "базовый URL"
        for line in self.lines[:30]:
            m = re.search(r':(\d{4})', line)
            if m and 'port' not in line.lower():
                self.service.port = int(m.group(1))
                break

    def _parse_endpoints(self) -> None:
        """Основной цикл: найти все эндпоинты в файле.

        Двухпроходный алгоритм:
        1. Собрать все заголовки уровня 2, 3, 4 с их позициями.
        2. Для каждого заголовка-эндпоинта определить границы контента
           и распарсить детали.
        """
        lines = self.lines

        # ── Фаза 1: собираем все заголовки ──
        headers: List[Tuple[int, str, int]] = []  # (idx, text, level)
        for idx, line in enumerate(lines):
            stripped = line.strip()
            m = re.match(r'^(#{2,4})\s+(.+)$', stripped)  # ##, ###, ####
            if m:
                level = len(m.group(1))
                headers.append((idx, m.group(2).strip(), level))

        # ── Фаза 2: определяем для каждого заголовка его role и group ──
        current_group = ""
        groups: Dict[int, str] = {}  # idx → group name
        endpoint_headers: List[Tuple[int, str, int]] = []  # (idx, text, level)
        skip_section: bool = False  # внутри не-эндпоинтной секции

        for i, (idx, text, level) in enumerate(headers):
            text_lower = text.lower()

            if level == 2:
                # ## заголовок — секция
                skip_section = False  # новая секция — сбрасываем
                gm = re.match(r'^группа\s+(.+)$', text_lower)
                if gm:
                    current_group = gm.group(1).strip()
                elif text_lower in _NON_ENDPOINT_HEADERS:
                    skip_section = True  # все ###/#### внутри этой секции — не эндпоинты
                else:
                    # Другая ## секция — может содержать эндпоинты
                    if not current_group:
                        current_group = text_lower
                continue

            if level in (3, 4):
                if skip_section:
                    continue  # пропускаем все ### внутри не-эндпоинтной секции
                # Проверяем, является ли это эндпоинтом
                if _is_endpoint_header(text):
                    endpoint_headers.append((idx, text, level))
                    groups[idx] = current_group

        # ── Фаза 3: для каждого эндпоинта определяем границы и парсим ──
        for i, (idx, text, level) in enumerate(endpoint_headers):
            # Граница: следующий эндпоинт того же или выше уровня
            # (т.е. level <= current_level)
            next_idx = len(lines)
            for j in range(i + 1, len(endpoint_headers)):
                next_ep_idx, _, next_level = endpoint_headers[j]
                if next_level <= level:
                    next_idx = next_ep_idx
                    break
            # Также проверяем, что не зашли за следующий ## заголовок
            for h_idx, h_text, h_level in headers:
                if h_idx > idx and h_level == 2 and h_idx < next_idx:
                    # ## заголовок внутри эндпоинта — тоже граница
                    next_idx = h_idx
                    break

            current_group = groups.get(idx, current_group)
            endpoint = self._parse_single_endpoint(text, current_group, idx)

            if endpoint:
                self._fill_endpoint_details(endpoint, idx + 1, next_idx)
                self.service.endpoints.append(endpoint)
            else:
                self.service.errors.append(
                    f"Не удалось распарсить эндпоинт на строке {idx + 1}: {text}"
                )

    def _parse_single_endpoint(
        self, header_text: str, current_group: str, line_idx: int
    ) -> Optional[MdEndpoint]:
        """Создать MdEndpoint из заголовка эндпоинта и ближайшего контекста."""
        # Ищем method + path в заголовке или в следующих строках
        method, path = None, None

        # Сначала в заголовке: "POST /auth/token — описание" или "4.1. POST /auth/token — описание"
        ep_match = re.search(r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\S]+)', header_text)
        if ep_match:
            method = ep_match.group(1)
            path = ep_match.group(2)
            title = header_text[ep_match.end():].lstrip(" —–-").strip()
        else:
            # Возможно, заголовок — просто название: "3.1. Список (плоский)"
            # Ищем method+path в следующих строках
            title = header_text
            for lookahead in range(1, 6):
                if line_idx + lookahead >= len(self.lines):
                    break
                lh = self.lines[line_idx + lookahead].strip()
                # Код-блок с method + path
                if lh.startswith("```"):
                    continue
                mp = _extract_method_path(lh)
                if mp:
                    method, path = mp
                    break

        if not method or not path:
            return None

        # Нормализуем путь: добавляем /api/v1 префикс если нужно
        # Пути в документации могут быть:
        #   /auth/token → /api/v1/auth/token
        #   /health → /health (health endpoint без префикса)
        #   /embed → /embed (TEI)
        if not path.startswith("/api/v1") and not path.startswith("/api/"):
            # Пути, которые точно имеют /api/v1 префикс (стандартные эндпоинты)
            if path.startswith("/auth/") or path.startswith("/admin/") or \
               path.startswith("/registry/") or path.startswith("/chat/") or \
               path.startswith("/text/") or path.startswith("/converter/") or \
               path.startswith("/validate/") or path.startswith("/internal/") or \
               path.startswith("/monitor/") or path.startswith("/system/") or \
               path.startswith("/documents/") or path.startswith("/drafts/") or \
               path.startswith("/tasks/") or path.startswith("/pages/") or \
               path.startswith("/rag/") or path.startswith("/integration/") or \
               path.startswith("/classifiers/") or path.startswith("/terminology/") or \
               path.startswith("/projects/"):
                path = f"/api/v1{path}"

        # Определяем group из пути, если не задан
        if not current_group:
            # Ищем группу в таблице содержания
            current_group = self._guess_group(path)

        return MdEndpoint(
            method=method,
            path=path,
            group=current_group,
            title=title,
        )

    def _guess_group(self, path: str) -> str:
        """Определить группу по пути."""
        # /api/v1/registry/classifiers/... → classifiers
        parts = path.strip("/").split("/")
        for p in parts:
            if p in ("auth", "admin", "chat", "text", "classifiers", "terminology",
                      "documents", "drafts", "pages", "monitor", "system",
                      "converter", "validate", "rag", "embed", "health"):
                return p
        return "common"

    def _fill_endpoint_details(
        self, endpoint: MdEndpoint, start: int, end: int
    ) -> None:
        """Заполнить детали эндпоинта: query-параметры, тело, ответы."""
        lines = self.lines

        # Собираем описание
        desc = _get_description_between(lines, start, end)
        if desc:
            endpoint.description = desc

        i = start
        in_code_block = False
        current_context: str = ""  # "query", "request", "response_200", etc.
        current_fields_table: List[str] = []  # строки текущей таблицы
        current_table_columns: List[str] = []
        current_table_start: int = -1

        while i < end:
            stripped = lines[i].strip()

            # ── Код-блоки ──
            if _is_code_block_start(stripped):
                block_start = i
                if stripped.lower().startswith("```json"):
                    json_data, next_i = _extract_json_from_code_block(lines, i)
                    i = next_i

                    # Определяем контекст: ответ или запрос
                    # Проверяем текст до код-блока
                    context_text = "\n".join(
                        lines[max(block_start - 3, 0):block_start]
                    ).lower()

                    if "ответ" in context_text:
                        sc = self._extract_status_code(context_text)
                        if endpoint.responses.get(sc) is None:
                            endpoint.responses[sc] = MdBody(status_code=sc)
                        endpoint.responses[sc].json_example = json_data
                    elif "запрос" in context_text or "body" in context_text:
                        if endpoint.request_body is None:
                            endpoint.request_body = MdBody(status_code="request")
                        endpoint.request_body.json_example = json_data
                else:
                    # Не JSON код-блок — просто пропускаем
                    i += 1
                    while i < end and not _is_code_block_end(lines[i].strip()):
                        i += 1
                    i += 1
                continue

            # ── Таблицы ──
            if _is_table_row(stripped):
                if _is_table_separator(stripped):
                    # Предыдущая строка была заголовком таблицы
                    if current_fields_table:
                        current_table_columns = _detect_table_columns(current_fields_table[-1])
                    current_fields_table = []
                    current_table_start = i + 1
                    i += 1
                    continue

                if current_table_start >= 0:
                    # Внутри таблицы — собираем строки данных
                    parsed = _parse_table_row(stripped, current_table_columns)
                    if parsed:
                        current_fields_table.append(stripped)

                    # Смотрим, что за таблица по окружающему контексту
                    context_start = max(current_table_start - 5, 0)
                    context_lines = lines[context_start:current_table_start]
                    context = "\n".join(context_lines).lower()
                    has_required_col = _has_required_column(current_table_columns)

                    # Определяем тип таблицы
                    if "query" in context or "параметр" in context:
                        # Query-параметры: если нет колонки "Обязательность",
                        # то все параметры опциональны (по умолчанию False)
                        field = self._parse_field_from_row(
                            parsed, current_table_columns,
                            default_required=has_required_col
                        )
                        if field:
                            endpoint.query_params.append(field)
                    elif "ответ" in context or "поля ответа" in context:
                        sc = self._extract_status_code(context)
                        if endpoint.responses.get(sc) is None:
                            endpoint.responses[sc] = MdBody(status_code=sc)
                        field = self._parse_field_from_row(
                            parsed, current_table_columns,
                            default_required=True
                        )
                        if field:
                            endpoint.responses[sc].fields.append(field)
                    elif "запрос" in context or "тело" in context or "body" in context:
                        if endpoint.request_body is None:
                            endpoint.request_body = MdBody(status_code="request")
                        field = self._parse_field_from_row(
                            parsed, current_table_columns,
                            default_required=True
                        )
                        if field:
                            endpoint.request_body.fields.append(field)

                    i += 1
                    continue
                else:
                    # Это может быть заголовок таблицы
                    current_fields_table = [stripped]
                    current_table_start = i + 1
                    i += 1
                    continue

            # Сброс контекста таблицы если вышли из таблицы
            if current_table_start >= 0:
                current_table_start = -1
                current_fields_table = []
                current_table_columns = []

            i += 1

        # ── Пост-обработка: мерджим JSON-примеры с таблицами полей ──
        self._merge_examples_with_fields(endpoint)

    def _parse_field_from_row(
        self, parsed: Dict[str, str], columns: List[str],
        default_required: bool = True,
    ) -> Optional[MdField]:
        """Распарсить строку таблицы в MdField."""
        if not parsed:
            return None

        # Ищем колонки по содержимому
        name = ""
        type_raw = ""
        required = True
        description = ""

        for col, val in parsed.items():
            stripped = val.strip()
            if col in ("поле", "параметр", "name", "field", "key"):
                name = stripped.strip("`").strip()
            elif col in ("тип", "type"):
                type_raw = stripped.strip("`").strip()
            elif col in ("обязательность", "обязательный", "required", "обяз."):
                required = self._is_required(stripped)
            elif col in ("описание", "description", "когда возникает", "когда"):
                description = stripped.strip("`").strip()
            else:
                # Если не можем определить колонку — эвристика:
                # первая неопознанная колонка → type
                if not type_raw and stripped:
                    type_raw = stripped.strip("`").strip()

        if not name:
            return None

        # Если в таблице нет колонки "Обязательность", используем default_required
        has_explicit_required = _has_required_column(columns)
        if not has_explicit_required:
            required = default_required

        return MdField(
            name=name,
            type_raw=type_raw,
            required=required,
            description=description,
        )

    def _is_required(self, value: str) -> bool:
        """Определить, обязательное ли поле."""
        cleaned = value.strip().lower().strip("`").strip()
        if cleaned in REQUIRED_MARKERS:
            return True
        if cleaned in OPTIONAL_MARKERS:
            return False
        # По умолчанию — обязательное
        return True

    def _extract_status_code(self, context: str) -> str:
        """Извлечь HTTP статус-код из контекста."""
        m = re.search(r'(?:ответ|status)\s*[`\s]*(\d{3})', context, re.IGNORECASE)
        if m:
            return m.group(1)
        # "Ответ 200:" или "200 OK"
        m = re.search(r'(\d{3})', context)
        if m:
            return m.group(1)
        return "200"

    def _merge_examples_with_fields(self, endpoint: MdEndpoint) -> None:
        """Объединить JSON-примеры с информацией из таблиц полей."""
        for sc, body in endpoint.responses.items():
            if body.json_example:
                schema = _build_schema_from_example(body.json_example)
                if body.fields:
                    schema = _merge_schema_with_fields(schema, body.fields)
                body.json_example = schema  # теперь это JSON Schema, а не пример
            elif body.fields:
                # Нет примера, строим только из таблицы
                schema: Dict[str, Any] = {"type": "object"}
                schema = _merge_schema_with_fields(schema, body.fields)
                body.json_example = schema

        if endpoint.request_body and endpoint.request_body.json_example:
            schema = _build_schema_from_example(endpoint.request_body.json_example)
            if endpoint.request_body.fields:
                schema = _merge_schema_with_fields(schema, endpoint.request_body.fields)
            endpoint.request_body.json_example = schema

    # ── Публичные утилиты ──────────────────────────────────────────

    @staticmethod
    def to_openapi(endpoints: List[MdEndpoint]) -> Dict[str, Any]:
        """Сконвертировать список MdEndpoint в OpenAPI 3.0.3 структуру (без генерации, заготовка)."""
        paths: Dict[str, Any] = {}
        for ep in endpoints:
            # Нормализуем путь: {param} → {param} — OpenAPI использует тот же формат
            path_item = paths.setdefault(ep.path, {})

            method_lower = ep.method.lower()
            operation: Dict[str, Any] = {
                "summary": ep.title,
                "description": ep.description,
                "tags": [ep.group] if ep.group else [],
                "parameters": [],
                "responses": {},
            }

            # Query-параметры
            for qp in ep.query_params:
                operation["parameters"].append({
                    "name": qp.name,
                    "in": "query",
                    "description": qp.description,
                    "required": qp.required,
                    "schema": {"type": _map_type(qp.type_raw)},
                })

            # Request body
            if ep.request_body and ep.request_body.json_example:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": ep.request_body.json_example,
                        }
                    },
                }

            # Responses
            for sc, body in ep.responses.items():
                resp_schema = body.json_example if body.json_example else {"type": "object"}
                operation["responses"][sc] = {
                    "description": body.description or f"HTTP {sc}",
                    "content": {
                        "application/json": {
                            "schema": resp_schema,
                        }
                    },
                }

            path_item[method_lower] = operation

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "API Documentation (from md)",
                "version": "0.1.0-md",
                "description": "Auto-generated from docs/api/*.md",
            },
            "paths": paths,
        }


# ── CLI для отладки ──────────────────────────────────────────────────

def main():
    """Тестовый запуск парсера на одном файле."""
    import sys

    if len(sys.argv) < 2:
        print("Использование: python -m service_checker.core.md_parser <path_to.md>")
        sys.exit(1)

    filepath = sys.argv[1]
    parser = MdApiParser(filepath)
    service = parser.parse()

    print(f"Сервис: {service.name} (key={service.key}, port={service.port})")
    print(f"Эндпоинтов: {len(service.endpoints)}")
    print(f"Ошибок парсинга: {len(service.errors)}")
    print()

    for ep in service.endpoints:
        print(f"  {ep.method} {ep.path}")
        print(f"    Группа: {ep.group}")
        print(f"    Название: {ep.title}")
        if ep.description:
            print(f"    Описание: {ep.description[:100]}")
        if ep.query_params:
            print(f"    Query-параметры: {len(ep.query_params)}")
            for qp in ep.query_params:
                print(f"      - {qp.name}: {qp.type_raw} (req={qp.required})")
        if ep.request_body:
            print(f"    Тело запроса: есть")
        for sc, body in ep.responses.items():
            has_schema = body.json_example is not None
            has_fields = len(body.fields) > 0
            print(f"    Ответ {sc}: schema={'да' if has_schema else 'нет'}, "
                  f"fields={len(body.fields)}")

    if service.errors:
        print(f"\n⚠️ Ошибки:")
        for err in service.errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
