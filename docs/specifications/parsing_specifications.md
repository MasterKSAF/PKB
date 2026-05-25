1. Контракт API (финальный)

### POST /ocr/process — запуск обработки

**Запрос:** `task_id` (от Оркестратора), `version_id`, `file_key`, опционально `options` (выбор движка, языка, флаги извлечения таблиц/изображений/классификации).

**Ответ `202`:** `task_id`, `status`, `version_id`, `estimated_completion`.

Идентификатор задачи (`task_id`) генерируется Оркестратором, передаётся в OCR-сервис и используется для всех последующих операций — longpoll-ожидания статуса и получения результата.

### GET /ocr/process/{task_id}/status — статус обработки (longpoll)

**Ответ `200`:** `task_id`, `status`, `progress_percent`, `pages_processed`, `pages_total`, `avg_confidence`, `started_at`, `completed_at`, а также `step` (текущий шаг обработки) и `step_detail`.

| `step` | Описание |
|---|---|
| `downloading` | Скачивание PDF из MinIO |
| `splitting` | Разбивка на страницы |
| `ocr_pages` | Распознавание страниц |
| `extracting_tables` | Извлечение таблиц |
| `extracting_images` | Извлечение и загрузка изображений |
| `classifying` | Классификация (МКС, ОКСТУ, УДК) |
| `aggregating` | Сборка итогового JSON |

### GET /ocr/process/{task_id}/result — итоговый JSON

**Ответ `200`:** JSON-контейнер со структурой документа (`structure`: секции, таблицы, изображения), классификацией (`classification`: коды МКС/ОКСТУ/УДК), оценкой качества (`quality`: общая и постраничная), массивом ошибок/предупреждений (`errors`) и общим статусом.

### Коды ошибок OCR-сервиса

| `error.code` | HTTP | Описание |
|---|---|---|
| `FILE_NOT_FOUND` | 404 | Файл не найден в MinIO |
| `FILE_TOO_LARGE` | 413 | PDF > 500 MB / > 2000 страниц |
| `UNSUPPORTED_FORMAT` | 415 | Не PDF / не изображение |
| `ENGINE_UNAVAILABLE` | 503 | Запрошенный OCR-движок недоступен |
| `OCR_FAILED` | 500 | Критическая ошибка распознавания |
| `STORAGE_ERROR` | 502 | Ошибка доступа к MinIO |
| `TASK_NOT_FOUND` | 404 | task_id не существует или протух |
| `TASK_EXPIRED` | 410 | Результат удалён (старше N дней) |

---

## 2. Внутренняя архитектура OCR-сервиса

Ключевое требование: **другая группа может разрабатывать и тестировать без внешних зависимостей**. Достигается через адаптеры.

### 2.1 Слои

```
┌─────────────────────────────────────────┐
│  api/                                   │  ← FastAPI роуты, Pydantic схемы
│    routes.py          вход/выход HTTP   │
│    schemas.py         модели запросов   │
├─────────────────────────────────────────┤
│  pipeline/                              │  ← Бизнес-логика пайплайна
│    orchestrator.py    шаги + координация │
│    steps/                               │
│      downloader.py    скачать PDF       │
│      splitter.py      PDF → страницы    │
│      ocr.py           распознавание     │
│      table_extractor.py                 │
│      image_extractor.py                 │
│      classifier.py    коды классификации│
│      aggregator.py    сборка JSON       │
├─────────────────────────────────────────┤
│  adapters/                              │  ← Точка подмены для тестов
│    storage.py         MinIO / Fake      │
│    ocr_engine.py      Paddle/Tesseract/Docling / Fake │
│    table_engine.py    детектор таблиц / Fake           │
├─────────────────────────────────────────┤
│  state/                                 │  ← Управление состоянием задач
│    manager.py         MemoryCache (любая реализация: Redis, in-memory и т.д.) │
└─────────────────────────────────────────┘
```

### 2.2 Адаптеры — ключ к тестируемости

```python
# adapters/storage.py
from abc import ABC, abstractmethod
from pathlib import Path

class StorageAdapter(ABC):
    """Абстракция над файловым хранилищем."""
    
    @abstractmethod
    async def download(self, file_key: str) -> Path:
        """Скачать файл из хранилища → локальный путь."""
        ...
    
    @abstractmethod
    async def upload(self, local_path: Path, remote_path: str) -> str:
        """Загрузить файл в хранилище → публичный путь."""
        ...
    
    @abstractmethod
    async def exists(self, file_key: str) -> bool:
        """Проверить существование файла."""
        ...


# adapters/ocr_engine.py
from dataclasses import dataclass, field

@dataclass
class OCRPageResult:
    text: str
    confidence: float
    bboxes: list[dict]           # bounding boxes слов/строк
    page_number: int
    errors: list[str] = field(default_factory=list)

class OCREngineAdapter(ABC):
    """Абстракция над OCR-движком."""
    
    @property
    @abstractmethod
    def engine_id(self) -> str: ...
    
    @abstractmethod
    async def recognize(self, image_path: Path, language: str) -> OCRPageResult: ...
```

### 2.3 Фейковые реализации для тестов

```python
# tests/conftest.py (или adapters/fake_*.py в самой библиотеке)
class FakeStorageAdapter(StorageAdapter):
    def __init__(self, files: dict[str, bytes] | None = None):
        self._files = files or {}
        self._uploads: dict[str, Path] = {}  # remote_path → local_path
    
    async def download(self, file_key: str) -> Path:
        if file_key not in self._files:
            raise FileNotFoundError(file_key)
        path = Path(f"/tmp/test_storage/{file_key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self._files[file_key])
        return path
    
    async def upload(self, local_path: Path, remote_path: str) -> str:
        self._uploads[remote_path] = local_path
        return f"fake://storage/{remote_path}"
    
    async def exists(self, file_key: str) -> bool:
        return file_key in self._files

class FakeOCREngine(OCREngineAdapter):
    engine_id = "fake"
    
    def __init__(self, pages: dict[int, str] | None = None):
        """pages: {page_number: text} — предопределённый результат."""
        self._pages = pages or {}
    
    async def recognize(self, image_path: Path, language: str) -> OCRPageResult:
        page_num = int(image_path.stem.split("_")[-1])  # page_001.png → 1
        text = self._pages.get(page_num, f"Page {page_num} text")
        return OCRPageResult(
            text=text,
            confidence=0.95,
            bboxes=[],
            page_number=page_num,
        )
```

### 2.4 Пайплайн — оркестратор шагов внутри сервиса

```python
# pipeline/orchestrator.py
from adapters.storage import StorageAdapter
from adapters.ocr_engine import OCREngineAdapter
from state.manager import StateManager

class OCRPipeline:
    def __init__(
        self,
        storage: StorageAdapter,
        ocr_engine: OCREngineAdapter,
        state: StateManager,
    ):
        self.storage = storage
        self.ocr = ocr_engine
        self.state = state
    
    async def process(self, task_id: str, file_key: str, options: dict, max_pages: int | None = None) -> dict:
        """Главный метод. Выполняет все шаги, возвращает итоговый JSON."""
        await self.state.set_step(task_id, "downloading")
        
        # Шаг 1: скачать PDF
        pdf_path = await self.storage.download(file_key)
        
        # Шаг 2: разбить на страницы
        await self.state.set_step(task_id, "splitting")
        page_images = await split_pages(pdf_path)  # → [Path("page_001.png"), ...]
        total = len(page_images)
        if max_pages is not None:
            page_images = page_images[:max_pages]
            total = len(page_images)
        await self.state.set_progress(task_id, pages_total=total)
        
        # Шаг 3: OCR страниц (параллельно)
        await self.state.set_step(task_id, "ocr_pages")
        ocr_results = []
        for i, img in enumerate(page_images):
            result = await self.ocr.recognize(img, options.get("language", "ru"))
            ocr_results.append(result)
            await self.state.set_progress(
                task_id, 
                pages_processed=i+1, 
                pages_total=total,
                avg_confidence=mean(r.confidence for r in ocr_results)
            )
        
        # Шаг 4: таблицы
        await self.state.set_step(task_id, "extracting_tables")
        tables = await extract_tables_from_pages(ocr_results, page_images)
        
        # Шаг 5: изображения (извлечь → загрузить в MinIO)
        await self.state.set_step(task_id, "extracting_images")
        images = await extract_and_upload_images(
            page_images, self.storage, options.get("version_id")
        )
        
        # Шаг 6: классификация
        await self.state.set_step(task_id, "classifying")
        classification = await classify_document(ocr_results)
        
        # Шаг 7: агрегация
        await self.state.set_step(task_id, "aggregating")
        result = aggregate_json(
            text_results=ocr_results,
            tables=tables,
            images=images,
            classification=classification,
            document_id=options.get("document_id"),
            version_id=options.get("version_id"),
        )
        
        return result
```

### 2.5 Управление состоянием (без БД)

```python
# state/manager.py
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class StateManager(ABC):
    @abstractmethod
    async def create(self, task_id: str, file_key: str, version_id: str, preview: bool = False) -> None: ...
    @abstractmethod
    async def set_step(self, task_id: str, step: str) -> None: ...
    @abstractmethod
    async def set_progress(self, task_id: str, **kwargs) -> None: ...
    @abstractmethod
    async def set_result(self, task_id: str, result: dict) -> None: ...
    @abstractmethod
    async def set_error(self, task_id: str, error: dict) -> None: ...
    @abstractmethod
    async def get(self, task_id: str) -> dict: ...
    @abstractmethod
    async def delete(self, task_id: str) -> None: ...
```

**Пример реализации — MemoryCache на Redis:**
- Например, в Redis: ключ `ocr:task:{task_id}` → хеш с полями `status`, `step`, `progress`, `started_at`, `result` (JSON-строка)
- TTL (настраивается в зависимости от реализации, например, 24 часа после `completed` / `failed`)

**Test-реализация — `dict` в памяти:**

```python
class MemoryStateManager(StateManager):
    def __init__(self):
        self._tasks: dict[str, dict] = {}
    
    async def create(self, task_id, file_key, version_id, preview=False):
        self._tasks[task_id] = {
            "status": "accepted",
            "file_key": file_key,
            "version_id": version_id,
            "preview": preview,
            "step": None,
            "progress_percent": 0,
            "pages_processed": 0,
            "pages_total": 0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "result": None,
        }
    
    async def set_step(self, task_id, step):
        self._tasks[task_id]["step"] = step
    
    # ... и т.д.
```

---

## 3. Как тестировать без внешних зависимостей

```python
# tests/test_pipeline.py
import pytest
from pipeline.orchestrator import OCRPipeline
from adapters.storage import FakeStorageAdapter
from adapters.ocr_engine import FakeOCREngine
from state.manager import MemoryStateManager

SAMPLE_PDF_BYTES = open("tests/fixtures/gost_2page.pdf", "rb").read()

@pytest.fixture
def pipeline():
    storage = FakeStorageAdapter(files={"file-001": SAMPLE_PDF_BYTES})
    ocr = FakeOCREngine(pages={
        1: "ГОСТ Р 12345-77\n\n1. Общие положения\nНастоящий стандарт...",
        2: "Продолжение таблицы 1...",
    })
    state = MemoryStateManager()
    return OCRPipeline(storage=storage, ocr_engine=ocr, state=state)

@pytest.mark.asyncio
async def test_full_pipeline(pipeline):
    task_id = "test-task-001"
    await pipeline.state.create(task_id, "file-001", "v1")
    
    result = await pipeline.process(task_id, "file-001", {
        "language": "ru",
        "extract_tables": True,
        "extract_images": True,
        "version_id": "v1",
        "document_id": "doc-test",
    })
    
    assert result["structure"]["title"] == "ГОСТ Р 12345-77"
    assert result["quality"]["pages_processed"] == 2
    assert result["status"] == "completed"
    assert len(result["structure"]["sections"]) > 0

@pytest.mark.asyncio
async def test_ocr_page_failure_doesnt_crash_pipeline(pipeline):
    """Одна страница с ошибкой — остальные обработаны."""
    ocr = FakeOCREngine(pages={1: "OK"})  # page 2 не распознана
    pipeline.ocr = ocr
    
    result = await pipeline.process(...)
    assert result["quality"]["pages_failed"] == 1
    assert result["status"] == "completed"  # не failed!

@pytest.mark.asyncio
async def test_preview_mode_first_3_pages(pipeline):
    """Preview mode — обрабатываются только первые 3 страницы."""
    task_id = "test-preview-001"
    await pipeline.state.create(task_id, "file-001", "v1", preview=True)
    
    result = await pipeline.process(task_id, "file-001", {
        "language": "ru",
        "version_id": "v1",
        "document_id": "doc-preview",
    }, max_pages=3)
    
    assert result["quality"]["pages_processed"] == 3
    assert result["status"] == "completed"
    assert pipeline.state._tasks[task_id]["preview"] is True
```

Ни одного поднятого Redis, MinIO, или Tesseract.

---

## 4. Что Orchestrator должен уметь (минимальные изменения)

Сейчас Orchestrator на пре-стейдже делает:
1. Принять файл от пользователя
2. Вычислить SHA-256
3. Загрузить в MinIO → получить `file_key`
4. Вернуть `202 { task_id }`

Добавляется (двухфазный пайплайн):

**Фаза Preview:**
1. Определить тип файла (скан/изображение → OCR, цифровой PDF/DOC → Parser)
2. Вызвать `POST /ocr/preview` или `POST /parser/preview` с `max_pages=3`
3. Получить частичный сырой JSON (первые N страниц)
4. Передать в Converter-validator (preview API): `POST /converter/preview/metadata`
5. Выполнить проверку уникальности: **Оркестратор → Registry**: `POST /registry/documents/check-uniqueness` (с метаданными из шага 4)
6. Отобразить пользователю метаданные и кандидатов в дубликаты
7. Ожидать решение пользователя: `proceed` / `stop_duplicate` / `force_new_version`

**Фаза Full (при `proceed`):**
1. Вызвать `POST /ocr/process` или `POST /parser/process` (полный режим, без `max_pages`)
   - Получить `task_id`
   - Ожидание результата через longpoll: `GET /ocr/process/{task_id}/status?longpoll=15`
     - При завершении → сразу ответ
     - При таймауте 15c → ответ с прогрессом, повтор longpoll
   - При `status: completed` → `GET /ocr/process/{task_id}/result`
2. Передать полный сырой JSON в Converter-validator: `POST /converter/convert`
3. Выполнить проверку уникальности (Оркестратор): `POST /registry/documents/check-uniqueness`
4. Если дубликат не найден — передать иерархический JSON в Registry: `POST /registry/documents`
5. Передать плоский JSON (секции) в RAG Builder: `POST /rag/build`

**Особенности preview-режима:**
- Параметр `?preview=true` (или `max_pages=N`) в `POST /ocr/preview` / `POST /parser/preview`
- Preview-ответ: без `file_key`, без сохранения бинарных объектов
- Сервис не использует LLM в preview-режиме
- Оркестратор хранит preview-данные в журнале пайплайна (не в БД)

**Контракт не меняется.** Вся логика ожидания результата описана в `common.md` (модель async с longpoll).

---

## 5. Резюме: что даёт такая архитектура

| Свойство | Как достигнуто |
|---|---|
| **Автономность OCR-сервиса** | Сам ходит в MinIO, сам складывает изображения, сам управляет своим стейтом |
| **Тестируемость без инфраструктуры** | Storage, OCR, State — адаптеры. Тесты на фейках, без внешних зависимостей (MinIO, MemoryCache и т.д.) |
| **Управляемость Оркестратором** | 4 эндпоинта (`process`, `status`, `result`, `engines`), JSON-контейнер как чёрный ящик |
| **Большие документы** | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO |
| **Готовые ссылки на изображения** | OCR сам выгружает в MinIO, отдаёт `file_key` в ответе |
| **Независимая разработка** | Другая группа может писать и тестировать OCR-сервис, имея только контракт API и интерфейсы адаптеров |