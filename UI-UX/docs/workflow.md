# Workflow

## Базовая схема

1. Переключиться на `develop`
2. Обновить ветку
3. Создать свою ветку под задачу
4. Сделать изменения
5. Проверить запуск
6. Закоммитить
7. Запушить ветку
8. Создать Pull Request в `develop`

## Пример

```bash
git checkout develop
git pull
git checkout -b feature/ui-chat
```

После изменений:

```bash
git add .
git commit -m "feat: update chat layout"
git push -u origin feature/ui-chat
```

## Правила

- Не пушим напрямую в `main`
- Не пушим в `develop` без необходимости
- Одна задача — одна ветка
- Один PR — один логический набор изменений
