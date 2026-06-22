# Архитектурные ориентиры

## Ленивая инициализация HTTP-клиента

**Проблема**: `httpx.AsyncClient()` загружает SSL-сертификаты при создании (~0.37s).  
`PipelineRunner` и `ApiCoverageTester` создавали клиент в `__init__`, из-за чего каждый unit-тест платил ~0.4s, даже если клиент сразу заменялся моком.

**Решение**: `httpx.AsyncClient` создаётся лениво — при первом реальном обращении к `self.client`.  
Реализовано через `@property` + приватный `_client`. Сеттер позволяет DI (подстановка мока в тестах).

**Паттерн**:
```python
self._client: Optional[httpx.AsyncClient] = None

@property
def client(self) -> httpx.AsyncClient:
    if self._client is None:
        self._client = httpx.AsyncClient(timeout=self.timeout)
    return self._client

@client.setter
def client(self, value: httpx.AsyncClient) -> None:
    self._client = value
```

**Где применяется**:
- `pipelines/base.py` — `PipelineRunner`
- `core/api_coverage_test.py` — `ApiCoverageTester`
