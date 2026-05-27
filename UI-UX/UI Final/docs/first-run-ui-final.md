# Первый запуск UI Final

Инструкция для локального запуска объединенной версии интерфейса.

## 1. Что установить

Нужно установить:

- Git for Windows;
- Docker Desktop;
- браузер Chrome, Edge или другой современный браузер.

Для запуска без Docker дополнительно нужен Node.js LTS.

## 2. Забрать только UI Final

Для запуска UI Final не обязательно забирать все рабочие материалы проекта. Удобный вариант - скачать ZIP ветки `feature/ui-final` с GitHub и открыть только папку:

```text
UI-UX/UI Final/frontend
```

Если нужна работа именно через Git, можно использовать sparse checkout, чтобы забрать только папку `UI-UX/UI Final`.

```bash
git clone --filter=blob:none --sparse https://github.com/NeuronsUII/PKB_neuroassistant.git
cd PKB_neuroassistant
git checkout feature/ui-final
git sparse-checkout set "UI-UX/UI Final"
cd "UI-UX/UI Final/frontend"
```

## 3. Альтернатива: обычное клонирование

Открыть Git Bash или терминал и перейти в папку, где будет храниться проект.

Пример:

```bash
cd /c/Users/Misha/Documents/GitHub
```

Клонировать репозиторий:

```bash
git clone https://github.com/NeuronsUII/PKB_neuroassistant.git
```

Перейти в проект:

```bash
cd PKB_neuroassistant
```

Переключиться на ветку объединенного интерфейса:

```bash
git checkout feature/ui-final
```

Перейти в папку фронтенда:

```bash
cd "UI-UX/UI Final/frontend"
```

## 4. Запуск через Docker

Docker Desktop должен быть запущен.

Команда запуска:

```bash
docker compose up --build
```

Открыть интерфейс:

```text
http://localhost:3000
```

Остановить проект можно в том же терминале:

```bash
Ctrl+C
```

Если нужно полностью остановить контейнер:

```bash
docker compose down
```

## 5. Запуск без Docker

Этот вариант нужен разработчику, если надо быстро править код и смотреть изменения.

Установить зависимости:

```bash
npm ci
```

Запустить dev-сервер:

```bash
npm run dev -- --host 127.0.0.1 --port 3310 --strictPort
```

Открыть интерфейс:

```text
http://127.0.0.1:3310
```

## 6. Проверка сборки

Проверить production-сборку:

```bash
npm run build
```

Проверить TypeScript:

```bash
npm run lint
```

## 7. Демо-вход

Можно вручную ввести логин и пароль или нажать одну из карточек роли на экране входа.

| Роль | Логин | Пароль |
| --- | --- | --- |
| Пользователь | `s.orlov` | `demo` |
| Администратор знаний | `a.volkova` | `demo` |
| Системный администратор | `i.smirnov` | `demo` |

## 8. Если порт занят

Если `3000` занят при Docker-запуске, нужно остановить другой контейнер или изменить порт в `docker-compose.yml`.

Если `3310` занят при dev-запуске, можно выбрать другой порт:

```bash
npm run dev -- --host 127.0.0.1 --port 3311 --strictPort
```

## 9. Важно

Сейчас UI работает на демонстрационных данных. Для работы с реальными документами, пользователями, историей и проверками нужна стыковка с Gateway и backend-сервисами.
