1. Контракт API (актуальная спецификация — в API-файлах)

Актуальный контракт OCR-сервиса — [`ocr_service_api.md`](../api/ocr_service_api.md), Parser-сервиса — [`parser_service_api.md`](../api/parser_service_api.md).

Оба сервиса имеют единый эндпоинт `POST /{ocr|parser}/process` с полем `mode: "preview" | "full"` (схлопнуты с отдельного `/preview`, решение 08.06).

Ниже приведена архитектура внутренней реализации, не привязанная к конкретной версии API.

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

## 4. Что Orchestrator должен уметь

Актуальное описание двухфазного пайплайна (preview → full), включая логику Orchestrator, — в [`pipeline1-formation.md`](../pipelines/pipeline1-formation.md).

Ниже — архитектурные детали, не попавшие в описание пайплайна (см. раздел 2 «Внутренняя архитектура OCR-сервиса»).

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

---

## 6. Риски внешних OCR-движков и компенсации (P3-6)

> **Статус**: 🟠 P3-6 — требует фиксации риска для конфиденциальных документов.

### 6.1. Использование Lama Parser (облачный сервис)

Lama Parser (внешний API, провайдер — `lamainfo.com` или альтернативы) — используется как fallback для сложных PDF (многоуровневая вёрстка, формулы, смешанные языки), когда локальные движки дают низкое качество.

**Риск**: Lama Parser — **облачный сервис**. Содержимое документа (включая конфиденциальные проекты, например, проекты судов с грифом) передаётся на внешний сервер.

**Компенсирующие меры (обязательны для проектов с грифом):**

1. **Конфигурация**: `app_settings.parser.lama_enabled = false` для проектов с грифом «конфиденциально» и выше. Контроль на стороне Orchestrator при выборе движка.
2. **Логирование**: при каждом вызове Lama Parser в лог пишется INFO с `lama_call_id` (для аудита). В `quality.notifications[]` ответа добавляется `{code: "LAMA_FALLBACK_USED", severity: "warning", category: "quality"}`.
3. **Альтернативы**: при отключённом Lama Parser — fallback на локальные движки (Tesseract, EasyOCR, PaddleOCR), даже при сниженном качестве. В таком случае черновик переходит в `review_required` (P1-20) для ручной проверки.
4. **Документирование**: для каждого проекта/документа с грифом в `registry.documents.status_note` указывается «конфиденциально — Lama отключён».
5. **Self-hosted альтернатива** (в roadmap, Sprint 5+): развёртывание self-hosted Lama Parser внутри Docker-сети `internal`, без передачи данных наружу.

### 6.2. Другие внешние OCR-движки

| Движок | Тип | Риск конфиденциальности | Компенсация |
|--------|-----|--------------------------|-------------|
| Tesseract | Open-source, локальный | Нет | — |
| EasyOCR | Open-source, локальный | Нет | — |
| PaddleOCR | Open-source, локальный | Нет | — |
| Cloud Vision API (Google) | Облачный | Высокий | Отключён по умолчанию, требует явного opt-in |
| AWS Textract | Облачный | Высокий | Отключён по умолчанию |
| **Lama Parser** | **Облачный** | **Средний-высокий** | **Конфигурируемо, см. §6.1** |
| Azure Form Recognizer | Облачный | Высокий | Отключён по умолчанию |

> **Запрещено** (по умолчанию) передавать документы с грифом «конфиденциально» и выше в облачные OCR-сервисы. Контроль — через `app_settings.parser.allowed_engines_for_classification` (конфигурируется per-проект).