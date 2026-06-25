# Guide — архитектурные решения и стиль

## Правила диагностики серверных ошибок

При жалобе «сервер не работает / ошибка» — не гадать, а собирать диагностику системно:

1. **Gateway diagnostics** (публичный, не требует auth):
   - `GET /api/v1/system/diagnostics` — быстрая сводка
   - `GET /api/v1/system/diagnostics?verbose=true` — полная (dmesg, порты, диски)
   - `GET /api/v1/system/diagnostics/{service}` — по конкретному сервису
   - `GET /api/v1/system/diagnostics/system` — логи ядра

2. **Health endpoints:**
   - `GET /api/v1/health` — gateway health
   - Прямые запросы к сервисам (если порты открыты): 8083 query, 8084 registry, 8091 rag-search, 7997 infinity

3. **Что смотреть в verbose diagnostics в первую очередь:**
   - `[System]` Memory/Swap — не забита ли память
   - `[Kernel]` — OOM kills (искать `Out of memory: Killed process`)
   - `[Memory pressure]` — не перегружена ли система
   - `[Ports]` — какие сервисы реально слушают порты

4. **Если docker логи недоступны** (SSH нет):
   - diagnostics показывает stderr docker — ошибка `error: no such object` значит контейнер не запущен или docker CLI не работает
   - dmesg из diagnostics — основной источник для OOM/kernel
   - SSH на сервер: `docker logs pkb-{service} --tail 50`

5. **Цепочка отказа:** начинать с downstream — если сервис Б не отвечает, смотреть его зависимости (сервис А, от которого он зависит). OOM одного сервиса валит всю цепочку.
