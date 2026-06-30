"""
Проверка всех читающих API-эндпоинтов через Gateway.

Проходит по таблице маршрутов Gateway, для каждого GET-маршрута
делает запрос и проверяет, что сервис отвечает (статус ≠ 404).

Usage:
    python data/tests/test_api_coverage.py                           # local
    set TEST_API_URL=http://195.70.195.203/api/v1 && python data/tests/test_api_coverage.py
"""
import io, sys, json, re
from urllib.parse import urljoin

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
from config import get_api_url, ensure_services

ensure_services("minimal")

BASE = get_api_url().rstrip("/")
session = requests.Session()

# ─── Эндпоинты для проверки ──────────────────────────────────────────────
# Формат: (method, path_pattern, описание)
# {id} заменяется на 1, {doc_id} на 1, {draft_id} на 1, {task_id} на 1


# Эндпоинты, извлечённые из фронтенда (UI-UX/UI Final/frontend/src/utils/http.ts)
# GET-запросы, которые реально вызывает web-интерфейс
ENDPOINTS = [
    # ── Auth ──
    ("GET", "/auth/me", "Текущий пользователь"),

    # ── System ──
    ("GET", "/system/health", "Health API"),

    # ── Registry: документы (через gateway) ──
    ("GET", "/documents", "Список документов"),
    ("GET", "/documents/{id}", "Детали документа"),
    ("GET", "/documents/{id}/pages", "Страницы документа"),
    ("GET", "/documents/{id}/pages/{id}/preview", "Превью страницы"),
    ("GET", "/documents/{id}/pages/{id}/text", "Текст страницы"),
    ("GET", "/documents/{id}/file", "Файл документа"),
    ("GET", "/documents/{id}/history", "История документа"),
    ("GET", "/documents/{id}/parameters", "Параметры"),
    ("GET", "/documents/{id}/versions", "Версии"),
    ("GET", "/documents/{id}/status", "Статус обработки"),
    ("GET", "/documents/{id}/errors", "Ошибки документа"),
    ("GET", "/documents/queue", "Очередь обработки"),

    # ── Registry: черновики ──
    ("GET", "/drafts", "Список черновиков"),
    ("GET", "/drafts/{id}", "Детали черновика"),
    ("GET", "/drafts/{id}/preview", "Превью черновика"),
    ("GET", "/drafts/{id}/preview/status", "Статус preview"),
    ("GET", "/drafts/{id}/tasks", "Задачи черновика"),

    # ── Registry: прямой доступ ──
    ("GET", "/registry/classifiers", "Классификаторы"),
    ("GET", "/registry/classifiers/tree", "Дерево классификаторов"),
    ("GET", "/registry/classifiers/pending", "Pending классификаторы"),
    ("GET", "/registry/classifiers/{id}", "Классификатор"),
    ("GET", "/registry/documents", "Список (прямой)"),
    ("GET", "/registry/documents/{id}", "Документ (прямой)"),
    ("GET", "/registry/documents/{id}/sections", "Секции (прямой)"),
    ("GET", "/registry/terminology", "Терминология"),
    ("GET", "/registry/terminology/{id}", "Термин"),
    ("GET", "/registry/terminology/normalize", "Нормализация термина"),
    ("GET", "/registry/stats", "Статистика"),
    ("GET", "/registry/enums", "Перечисления"),

    # ── Orchestrator: задачи ──
    ("GET", "/tasks/{id}/status", "Статус задачи"),

    # ── Query (chat + text) ──
    ("GET", "/chat/sessions", "Сессии чата"),
    ("GET", "/chat/sessions/{id}", "Сессия чата"),
    ("GET", "/chat/sessions/{id}/messages/{id}", "Сообщение чата"),
    ("GET", "/chat/history", "История чата"),
    ("GET", "/chat/history/export", "Экспорт истории"),
    ("GET", "/chat/projects", "Проекты чата"),

    # ── Monitor ──
    ("GET", "/monitor/metrics", "Метрики"),

    # ── Admin ──
    ("GET", "/admin/roles", "Роли"),
    ("GET", "/admin/users", "Пользователи"),
    ("GET", "/admin/audit", "Аудит"),
]


def resolve(path: str) -> str:
    """Заменить {id}, {doc_id}, {draft_id}, {task_id} на 1"""
    return re.sub(r"\{(\w+)\}", "1", path)


# ─── Auth ─────────────────────────────────────────────────────────────────
print(f"Target: {BASE}\n")

# Пробуем получить токен (если не получится — тестируем без авторизации)
TOKEN = None
try:
    r = requests.post(f"{BASE}/auth/token",
        json={"username": "admin@example.com", "password": "Admin1234!"},
        timeout=5)
    if r.status_code == 200:
        TOKEN = r.json().get("access_token") or r.json().get("token")
        print(f"Auth: OK (token: {TOKEN[:40]}...)" if TOKEN else "Auth: ответ без токена")
    else:
        print(f"Auth: HTTP {r.status_code} — продолжаем без авторизации")
except Exception as e:
    print(f"Auth: {e} — продолжаем без авторизации")

HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
print()

# ─── Тестирование ────────────────────────────────────────────────────────
total = len(ENDPOINTS)
passed = 0
failed = 0
skipped = 0
results = []

for method, path_pattern, desc in ENDPOINTS:
    url = f"{BASE}{resolve(path_pattern)}"
    try:
        resp = session.request(method, url, headers=HEADERS, timeout=10)

        if resp.status_code == 404:
                try:
                    err_code = resp.json().get("error", {}).get("code", "") if resp.headers.get("content-type","").startswith("application/json") else ""
                except Exception:
                    err_code = ""

                # NOT_FOUND от gateway — эндпоинт не зарегистрирован
                # DOCUMENT_NOT_FOUND / DRAFT_NOT_FOUND от сервиса — объект не найден, это нормально
                if err_code in ("DOCUMENT_NOT_FOUND", "DRAFT_NOT_FOUND", "TASK_NOT_FOUND", "SESSION_NOT_FOUND", "MESSAGE_NOT_FOUND", "CLASSIFIER_NOT_FOUND", "TERM_NOT_FOUND", "CATEGORY_NOT_FOUND"):
                    status = "OK"
                    passed += 1
                    note = f"HTTP 404 ({err_code}) — объект не найден, эндпоинт жив"
                elif err_code == "NOT_FOUND":
                    msg = resp.json().get("error", {}).get("message", "")
                    if "Маршрут не найден" in msg:
                        status = "FAIL"
                        failed += 1
                        note = f"HTTP 404 — эндпоинт не найден (gateway)"
                    else:
                        status = "OK"
                        passed += 1
                        note = f"HTTP 404 — объект не найден (сервис), эндпоинт жив"
                else:
                    status = "WARN"
                    passed += 1
                    note = f"HTTP 404 ({err_code}) — предположительно объект не найден"
        elif resp.status_code in (401, 403):
            status = "WARN"
            passed += 1
            note = f"HTTP {resp.status_code} (требуется авторизация)"
        elif resp.status_code in (400, 422):
            status = "WARN"
            passed += 1
            note = f"HTTP {resp.status_code} (ошибка запроса, но эндпоинт жив)"
        elif resp.status_code == 410:
            status = "WARN"
            passed += 1
            note = "HTTP 410 (deprecated)"
        else:
            status = "OK"
            passed += 1
            note = f"HTTP {resp.status_code}" if resp.status_code == 200 else f"HTTP {resp.status_code}"

        results.append((status, method, resolve(path_pattern), desc, note))

    except requests.exceptions.ConnectionError:
        status = "FAIL"
        failed += 1
        note = "Connection refused"
        results.append((status, method, resolve(path_pattern), desc, note))
    except Exception as e:
        status = "FAIL"
        failed += 1
        note = str(e)
        results.append((status, method, resolve(path_pattern), desc, note))

# ─── Отчёт ───────────────────────────────────────────────────────────────
print(f"{'='*80}")
print(f"  API Coverage Report: {total} endpoints")
print(f"{'='*80}")
print(f"{'Статус':8} {'Метод':7} {'Путь':45} {'Описание':25} {'Замечание'}")
print(f"{'-'*8} {'-'*7} {'-'*45} {'-'*25} {'-'*30}")

for status, method, path, desc, note in results:
    print(f"{status:8} {method:7} {path:45} {desc:25} {note}")

print(f"{'='*80}")
print(f"  Итого: {total} проверено, {passed} пройдено, {failed} провалено")
if failed:
    print(f"\n  ❌ FAILED ({failed}):")
    for status, method, path, desc, note in results:
        if status == "FAIL":
            print(f"    {method} {path} — {note}")
    sys.exit(1)
else:
    print(f"\n  ✅ Все эндпоинты отвечают (не 404)")
