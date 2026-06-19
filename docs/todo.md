# todo — правки по решению от 19.06

## Согласовано

- **IDOR** — удалён (CM-3, GW-6, раздел из common_api.md)
- **Checks** — убраны (из auth_service_api.md, добавлена GW-13)
- **ON DELETE/ON UPDATE** — не нужно (DB-5, P2-4 удалены, README.md changelog исправлен)
- **Rate limiting** — Nginx без Redis (CM-2, GW-4, все упоминания Redis в rate limiting удалены)
- **RBAC-матрица** — из Common в Registry (RG-12)
- **Матрица ответственных** — убраны счётчики

## OTEL SDK

- **Во всех сервисах** — восстановлено (CM-6, OR-8, monitoring.md, service_dependencies.md)
- **service_checker** — dev-only, CI без post-deploy

## Статус

Все изменения внесены.
