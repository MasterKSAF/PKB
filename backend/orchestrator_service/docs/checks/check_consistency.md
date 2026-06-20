# Правила проверки целостности документации

> Основа — структура из README.md. Перед любыми изменениями прогонять по чеклисту.

---

## 1. API (`docs/api/`)

Каждый файл в `api/` должен быть учтён в README.md. После изменения API-документа:

- [ ] Название файла совпадает с путём в README.md?
- [ ] Все эндпоинты, описанные в пайплайнах (`pipelines/`), есть в API-спецификации?
- [ ] Нет ли упоминаний удалённых концепций (IDOR, checks, Redis rate limiting)?

---

## 2. Пайплайны (`docs/pipelines/`)

- [ ] Каждый шаг пайплайна ссылается на конкретный эндпоинт API?
- [ ] FSM-статусы в пайплайне совпадают с enum в API-спецификации?
- [ ] Нет ли упоминаний удалённых технологий (Redis в rate limiting)?

---

## 3. База данных (`docs/database/`)

- [ ] Все `DB-*` задачи из `6.dev_tasks_17_06.md` отражены в `db_diagrams.md`?
- [ ] Типы полей в описаниях API совпадают с типами в схеме БД?
- [ ] Для удалённых `DB-*` задач — нет упоминаний в других документах?

---

## 4. Архитектура (`docs/architecture/`)

### monitoring.md
- [ ] OpenTelemetry SDK упомянут последовательно (не «только Gateway» без причины)?
- [ ] service_checker не ссылается на prod-окружение (post-deploy и т.д.)?
- [ ] SLO/SLI источники данных существуют (если OTel span — то OTEL SDK есть в сервисе)?

### service_dependencies.md
- [ ] У каждого сервиса одинаковый набор observability-пакетов (`opentelemetry-*`)?
- [ ] Redis не упомянут в rate limiting?
- [ ] Gateway имеет те же OTEL-зависимости, что и остальные (или явно прописанные версии)?

---

## 5. Глоссарий (`docs/glossary.md`)

- [ ] Все термины, используемые в API и пайплайнах, есть в глоссарии?
- [ ] Нет ли терминов, ссылающихся на удалённые концепции?
- [ ] service_checker помечен как dev-only?

---

## 6. Спецификации (`docs/specifications/`)

- [ ] После удаления задачи — проверить, не ссылается ли спецификация на неё?

---

## 7. Общие сквозные проверки

### Grep-паттерны (прогонять после изменений)

```bash
# Redis + rate limiting — нет совпадений
grep -r 'Redis.*rate\|rate.*Redis\|limit_req.*Redis' docs/ --include='*.md'

# IDOR — нет совпадений (кроме check_rule.md — там общий чеклист)
grep -r 'IDOR\|Insecure Direct' docs/ --include='*.md'

# ON DELETE как задача — нет совпадений
grep -r 'ON DELETE\|ON UPDATE' docs/ --include='*.md'

# service_checker post-deploy — нет совпадений
grep -r 'post-deploy\|Post-deploy' docs/ --include='*.md'
```

### Task-ID сверка

```bash
# Все CM-* GW-* OR-* DB-* RG-* RS-* QS-* из dev_tasks — нет ссылок в других docs (кроме todo)
grep -o '\b\(CM\|GW\|OR\|DB\|RG\|RS\|QS\)-\d\+' docs/ --include='*.md' \
  | sort -u | grep -v 'todo.md\|6.dev_tasks_17_06.md'
```

### Структура README

```bash
# Каждый .md в папках docs/ должен быть упомянут в README.md
# Каждый сервис из service_dependencies.md — упомянут в README.md
```

---

## 8. Что делать при изменении задачи в `6.dev_tasks_17_06.md`

1. **Удаление задачи** → grep по всем .md, убрать упоминания
2. **Добавление задачи** → проверить, что не дублируется
3. **Изменение технологии** (Redis → Nginx, OTEL только Gateway → все сервисы) → grep по всем .md
4. **Проверить README.md** — changelog, структуру папок, описание сервисов
5. **После правок в API/пайплайнах** — запустить `python checks/scripts/check_cross_references.py`
6. **После правок схем** — сверить с `docs/api/_schemas.md` (source of truth)
