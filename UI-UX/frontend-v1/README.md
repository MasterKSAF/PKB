# Frontend V1

Первая рабочая версия UI для PKB neuroassistant.

## Что внутри

- React + Vite
- Dockerfile для production-сборки
- `docker-compose.yml` для быстрого запуска
- `nginx.conf` для раздачи собранного SPA
- `.env.example` с базовой настройкой API

## Запуск локально

```bash
npm install
npm run dev
```

После запуска интерфейс доступен на:

- `http://localhost:3000`

## Запуск через Docker

```bash
docker compose up --build
```

После запуска интерфейс доступен на:

- `http://localhost:3000`

## Переменные окружения

Файл `.env.example` уже добавлен.

Базовая переменная:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Если нужен свой backend, можно создать локальный `.env` на основе `.env.example`.

## Что не коммитим

- `node_modules/`
- `dist/`
- `tmp/`
- временные скриншоты и локальные артефакты

## Команды

```bash
npm run dev
npm run build
npm run lint
```
