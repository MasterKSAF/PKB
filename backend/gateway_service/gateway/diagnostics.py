"""
PKB Neuroassistant — Diagnostics module (встроен в Gateway)

Собирает диагностику сервера: система, Docker, Git, логи, pipeline, очередь.
Работает через Docker socket (/var/run/docker.sock), HTTP к internal-сервисам, git.
"""

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

PROJECT_DIR = os.environ.get("PROJECT_DIR", "/project")
COMPOSE_PROJECT = "pkb"
HEALTH_SERVICES = [
    "pkb-postgres", "pkb-redis", "pkb-minio", "pkb-auth",
    "pkb-registry", "pkb-parser", "pkb-converter-validator",
    "pkb-rag-builder", "pkb-rag-search", "pkb-query",
    "pkb-orchestrator", "pkb-gateway",
]
# Контейнеры с префиксом pkb- (по умолчанию для service_diagnostics)
# Ключ — короткое имя, значение — имя контейнера (None если pkb-{key})
SERVICE_CONTAINERS: dict[str, str | None] = {
    # pkb-префикс (None = pkb-{name})
    "orchestrator": None,
    "parser": None,
    "converter-validator": None,
    "rag-builder": None,
    "rag-search": None,
    "registry": None,
    "auth": None,
    "query": None,
    "celery-worker": None,
    "frontend": None,
    "gateway": None,  # сам себе
    # Инфраструктура
    "postgres": None,
    "redis": None,
    "minio": None,
    "infinity": None,
    # Без префикса pkb-
    "docling-serve": "docling-serve-cpu",
}
KNOWN_SERVICES = set(SERVICE_CONTAINERS.keys())
# Внутренние HTTP endpoints сервисов (Docker network)
SERVICE_HTTP: dict[str, tuple[str, int]] = {
    "orchestrator": ("orchestrator", 8081),
    "registry": ("registry", 8084),
    "parser": ("parser", 8087),
    "converter-validator": ("converter-validator", 8086),
    "rag-builder": ("rag-builder", 8090),
    "rag-search": ("rag-search", 8091),
    "query": ("query", 8083),
    "auth": ("auth", 8082),
    "docling-serve": ("docling-serve-cpu", 5001),
}
START_TIME = time.time()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, timeout=10, cwd=None) -> str:
    """Запускает команду, возвращает stdout. При ошибке — stderr.

    timeout=10 — агрессивный таймаут: лучше показать (unreachable) чем ждать 30с.
    """
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        out = r.stdout.strip()
        if r.returncode != 0:
            err = r.stderr.strip()
            if err:
                return err
        return out
    except Exception as e:
        return str(e)


def run_lines(cmd, timeout=10, cwd=None) -> list:
    out = run(cmd, timeout, cwd=cwd)
    return out.split("\n") if out else []


def _git(cmd, timeout=10) -> str:
    """Запускает git-команду в PROJECT_DIR. Возвращает stdout при успехе, иначе пустую строку."""
    try:
        r = subprocess.run(['git'] + cmd, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_DIR)
        if r.returncode != 0:
            return ""
        return r.stdout.strip()
    except Exception:
        return ""


def _git_lines(cmd, timeout=30) -> list:
    return run_lines(['git'] + cmd, timeout, cwd=PROJECT_DIR)


# ---------------------------------------------------------------------------
# HTTP helper — опрос internal-сервисов
# ---------------------------------------------------------------------------

def _http_get(host: str, port: int, path: str, timeout=5) -> dict | list | str | None:
    """GET к internal-сервису, возвращает распаршенный JSON или None."""
    import socket
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        req = urllib.request.Request(f"http://{host}:{port}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            ct = resp.headers.get("Content-Type", "")
            if "application/json" in ct:
                return json.loads(body)
            return body
    except Exception:
        return None
    finally:
        socket.setdefaulttimeout(old_timeout)


# ---------------------------------------------------------------------------
# Блоки диагностики — Orchestrator / Pipeline
# ---------------------------------------------------------------------------

def orchestrator_tasks() -> list:
    """Статистика задач пайплайна + активные задачи + зависшие."""
    lines = []
    lines.append("[Pipeline: tasks]")

    stats = _http_get("orchestrator", 8081, "/api/v1/tasks/stats")
    if stats and isinstance(stats, dict):
        total = stats.get("total", 0)
        by_status = stats.get("by_status", {})
        by_stage = stats.get("by_stage", {})
        lines.append(f"  Total: {total}")
        lines.append(f"  By status: {by_status}")
        lines.append(f"  By stage:  {by_stage}")
    else:
        lines.append("  (unreachable)")

    # Активные задачи (status=active + их шаги)
    tasks_data = _http_get("orchestrator", 8081, "/api/v1/tasks/")
    if tasks_data and isinstance(tasks_data, (list, dict)):
        tasks = tasks_data if isinstance(tasks_data, list) else \
                tasks_data.get("tasks", tasks_data.get("items", []))
        active = [t for t in tasks if t.get("status") in ("active", "pending")]
        if active:
            lines.append(f"\n  Active tasks ({len(active)}):")
            for t in active:
                tid = t.get("task_id") or t.get("id")
                stage = t.get("pipeline_stage", "?")
                pct = t.get("progress_percent", 0)
                created = (t.get("created_at") or "")[:19]
                updated = (t.get("updated_at") or "")[:19]
                lines.append(f"    #{tid} stage={stage} {pct}% created={created} updated={updated}")

                # Шаги активной задачи
                steps = _http_get("orchestrator", 8081, f"/api/v1/tasks/{tid}/steps")
                if steps and isinstance(steps, (list, dict)):
                    step_list = steps if isinstance(steps, list) else steps.get("steps", [])
                    for s in step_list:
                        sn = s.get("step_name", "?")
                        st = s.get("status", "?")
                        ss = s.get("started_at", "") or ""
                        sc = s.get("completed_at", "") or ""
                        lines.append(f"      - {sn:25s} {st:12s} started={ss[:19]} completed={sc[:19]}")
        else:
            lines.append("\n  (no active tasks)")

        # Недавно завершённые (последние 5)
        completed = [t for t in tasks if t.get("status") == "completed"][-5:]
        if completed:
            lines.append(f"\n  Recently completed ({len(completed)}):")
            for t in completed:
                tid = t.get("task_id") or t.get("id")
                stage = t.get("pipeline_stage", "?")
                created = (t.get("created_at") or "")[:19]
                updated = (t.get("updated_at") or "")[:19]
                lines.append(f"    #{tid} stage={stage} created={created} finished={updated}")

    return lines


def orchestrator_queue() -> list:
    """Очередь документов (ожидающие / в обработке)."""
    lines = []
    lines.append("[Pipeline: document queue]")
    queue = _http_get("orchestrator", 8081, "/api/v1/documents/queue")
    if queue and isinstance(queue, dict):
        entries = queue.get("queue", queue.get("items", []))
        meta = queue.get("meta", {})
        lines.append(f"  Total in queue: {meta.get('total', len(entries))}")
        if entries:
            for e in entries[:10]:  # первые 10
                doc_id = e.get("document_id") or e.get("id", "?")
                status = e.get("status", "?")
                created = (e.get("created_at") or "")[:19]
                lines.append(f"    doc#{doc_id} status={status} created={created}")
    else:
        lines.append("  (unreachable or empty)")
    return lines


# ---------------------------------------------------------------------------
# Блоки диагностики — PostgreSQL (через docker exec)
# ---------------------------------------------------------------------------

def _psql(sql: str, timeout=5) -> str | None:
    """Выполнить SQL через docker exec в pkb-postgres, вернуть текст."""
    return run(
        ["docker", "exec", "pkb-postgres",
         "psql", "-U", "pkb", "-d", "pkb_neuro",
         "-t", "-A", "-c", sql],
        timeout=timeout,
    )


def _redis_cmd(cmd: str, timeout=5) -> str | None:
    """Выполнить команду Redis через docker exec."""
    return run(
        ["docker", "exec", "pkb-redis",
         "redis-cli", "-n", "0"] + cmd.split(),
        timeout=timeout,
    )


def pipeline_db_info() -> list:
    """Прямые SQL-запросы к pipeline.tasks и task_steps."""
    lines = []
    lines.append("[Pipeline: DB]")

    # Сводка по статусам
    summary = _psql("SELECT status, COUNT(*) FROM pipeline.tasks WHERE deleted_at IS NULL GROUP BY status ORDER BY status")
    if summary:
        lines.append("  Tasks by status:")
        for row in summary.split("\n"):
            row = row.strip()
            if row:
                parts = row.split("|")
                if len(parts) >= 2:
                    lines.append(f"    {parts[0]}: {parts[1]}")
    else:
        lines.append("  (DB unreachable)")

    # Задачи, running > 5 минут (потенциально зависшие)
    stuck = _psql(
        "SELECT id, status, pipeline_stage, current_step_name, "
        "EXTRACT(EPOCH FROM (NOW() - updated_at))::int AS stuck_sec "
        "FROM pipeline.tasks "
        "WHERE deleted_at IS NULL AND status IN ('active','pending') "
        "AND updated_at < NOW() - INTERVAL '5 minutes' "
        "ORDER BY updated_at"
    )
    if stuck and stuck.strip():
        lines.append("\n  Stuck tasks (>5min without update):")
        for row in stuck.split("\n"):
            row = row.strip()
            if row:
                parts = row.split("|")
                if len(parts) >= 5:
                    lines.append(f"    #{parts[0]} {parts[1]} stage={parts[2]} step={parts[3]} stuck={parts[4]}s")
    else:
        lines.append("\n  (no stuck tasks)")

    # Шаги в статусе running (по всем задачам)
    running_steps = _psql(
        "SELECT ts.task_id, ts.step_name, ts.status, "
        "EXTRACT(EPOCH FROM (NOW() - ts.started_at))::int AS running_sec, "
        "ts.started_at::text "
        "FROM pipeline.task_steps ts "
        "WHERE ts.deleted_at IS NULL AND ts.status IN ('running','pending') "
        "ORDER BY ts.task_id, ts.id"
    )
    if running_steps and running_steps.strip():
        lines.append("\n  Running/pending steps:")
        for row in running_steps.split("\n"):
            row = row.strip()
            if row:
                parts = row.split("|")
                if len(parts) >= 5:
                    lines.append(f"    task#{parts[0]} {parts[1]:25s} {parts[2]:10s} {parts[3]}s started={parts[4][:19]}")
    else:
        lines.append("\n  (no running steps)")

    return lines


def document_db_info() -> list:
    """Статистика документов registry через SQL."""
    lines = []
    lines.append("[Registry: DB stats]")

    total = _psql("SELECT COUNT(*) FROM registry.documents WHERE deleted_at IS NULL")
    if total and total.strip():
        lines.append(f"  Documents: {total.strip()}")
    else:
        lines.append("  (DB unreachable or empty)")
        return lines

    drafts = _psql("SELECT COUNT(*) FROM registry.drafts")
    if drafts and drafts.strip():
        lines.append(f"  Drafts: {drafts.strip()}")

    versions = _psql("SELECT COUNT(*) FROM registry.document_versions")
    if versions and versions.strip():
        lines.append(f"  Versions: {versions.strip()}")

    # Ошибки (последние 5)
    errs = _psql(
        "SELECT id, task_id, error_code, error_message, created_at::text "
        "FROM pipeline.tasks "
        "WHERE deleted_at IS NULL AND error_code IS NOT NULL "
        "ORDER BY created_at DESC LIMIT 5"
    )
    if errs and errs.strip():
        lines.append("\n  Recent task errors:")
        for row in errs.split("\n"):
            row = row.strip()
            if row:
                parts = row.split("|")
                if len(parts) >= 5:
                    lines.append(f"    #{parts[0]} task#{parts[1]} [{parts[2]}] {parts[3][:80]} @ {parts[4][:19]}")

    return lines


def celery_queue_info() -> list:
    """Очередь Celery через Redis."""
    lines = []
    lines.append("[Celery]")

    # Основная очередь
    qlen = _redis_cmd("LLEN celery")
    if qlen and qlen.strip():
        lines.append(f"  Queue 'celery': {qlen.strip()} items")
    else:
        qlen = _redis_cmd("LLEN celery")
        if qlen is None:
            lines.append("  (Redis unreachable)")
            return lines
        lines.append(f"  Queue 'celery': 0 items")

    # Другие очереди
    for q in ["celery.preview", "celery.full", "celery.registry", "celery.rag"]:
        items = _redis_cmd(f"LLEN {q}")
        if items and items.strip() and items.strip() != "0":
            lines.append(f"  Queue '{q}': {items.strip()} items")

    # Зарезервированные задачи
    reserved = _redis_cmd("LLEN celery.reserved")
    if reserved and reserved.strip() and reserved.strip() != "0":
        lines.append(f"  Reserved: {reserved.strip()} tasks")

    # Celery inspect — scheduled, active, reserved
    scheduled = _redis_cmd("ZCARD celery.scheduled")
    if scheduled and scheduled.strip() and scheduled.strip() != "0":
        lines.append(f"  Scheduled: {scheduled.strip()} tasks")

    return lines


# ---------------------------------------------------------------------------
# Блоки диагностики — Registry
# ---------------------------------------------------------------------------

def registry_info() -> list:
    """Статистика документов в реестре."""
    lines = []
    lines.append("[Registry: documents]")
    data = _http_get("registry", 8084, "/api/v1/registry/documents?limit=1")
    if data and isinstance(data, dict):
        total = data.get("meta", data).get("total", "?")
        lines.append(f"  Total documents: {total}")
    else:
        lines.append("  (unreachable)")
    return lines


# ---------------------------------------------------------------------------
# Блоки диагностики — система
# ---------------------------------------------------------------------------

def system_info() -> list:
    lines = []
    lines.append("[System]")
    lines.append(f"  Hostname: {run(['hostname'])}")
    lines.append(f"  Uptime:   {run(['uptime', '-p']) or run(['uptime'])}")
    lines.append(f"  Load:     {run(['uptime']).split('load average:')[-1].strip() if 'load average' in run(['uptime']) else '?'}")
    lines.append(f"  CPU:      {run(['nproc'])} cores")

    # Git commit и время последнего деплоя — см. Created в Health
    # Метка времени деплоя из /project/.deployed (создаётся deploy.sh)
    try:
        val = Path("/project/.deployed").read_text().strip()
        if val:
            lines.append(f"  Deploy:   {val}")
    except Exception:
        pass
    mem = run(['free', '-h']).split("\n")
    for m in mem:
        if m.startswith("Mem:"):
            parts = m.split()
            lines.append(f"  Memory:   {parts[2]} / {parts[1]}  (avail: {parts[6]})")
        elif m.startswith("Swap:"):
            parts = m.split()
            lines.append(f"  Swap:     {parts[2]} / {parts[1]}")
    return lines


def disk_usage() -> list:
    lines = []
    lines.append("[Disk]")
    df = run_lines(['df', '-h', '/', '/var/lib/docker'])
    for d in df[:5]:
        lines.append(f"  {d}")
    prj_size = run(['du', '-sh', PROJECT_DIR])
    if prj_size:
        lines.append(f"  Project: {prj_size}")
    docker_root = ""
    info = run(['docker', 'info'])
    for line in info.split("\n"):
        if "Docker Root Dir:" in line:
            docker_root = line.split("Docker Root Dir:")[-1].strip()
            break
    if docker_root:
        df_docker = run(['df', '-h', docker_root]).split("\n")
        if len(df_docker) > 1:
            p = df_docker[1].split()
            if len(p) >= 5:
                lines.append(f"  Docker:  {docker_root} ({p[2]} / {p[1]} ({p[4]})")
    return lines


def docker_df() -> list:
    lines = []
    lines.append("[Docker disk]")
    df = run_lines(['docker', 'system', 'df'])
    for d in df:
        lines.append(f"  {d}")
    return lines


def git_status() -> list:
    lines = []
    lines.append("[Git]")
    branch = _git(['rev-parse', '--abbrev-ref', 'HEAD'])
    if not branch:
        lines.append("  (not a git repository)")
        return lines
    commit = _git(['rev-parse', '--short', 'HEAD'])
    msg = _git(['log', '-1', '--pretty=%s'])
    lines.append(f"  Branch: {branch}")
    lines.append(f"  Commit: {commit}")
    lines.append(f"  Msg:    {msg}")
    status = _git(['diff', '--stat'])
    if status:
        lines.append(f"  Dirty:  {status.split(chr(10))[-1]}")
    else:
        lines.append(f"  Dirty:  clean")
    upstream = _git(['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}'])
    if upstream:
        upstream = upstream.replace("refs/remotes/", "")
        behind = _git(['rev-list', '--count', 'HEAD..@{upstream}'])
        ahead = _git(['rev-list', '--count', '@{upstream}..HEAD'])
        lines.append(f"  Remote:  {upstream}  (ahead {ahead}, behind {behind})")
    last = _git_lines(['log', '--oneline', '-5'])
    for l in last:
        lines.append(f"    {l}")
    return lines


def git_status_compact() -> list:
    lines = []
    lines.append("[Git]")
    branch = _git(['rev-parse', '--abbrev-ref', 'HEAD'])
    if not branch:
        lines.append("  (not a git repository)")
        return lines
    commit = _git(['rev-parse', '--short', 'HEAD'])
    lines.append(f"  Branch: {branch}")
    lines.append(f"  Commit: {commit}")
    status = _git(['diff', '--stat'])
    if status:
        lines.append(f"  Dirty:  {status.split(chr(10))[-1]}")
    else:
        lines.append(f"  Dirty:  clean")
    return lines


def docker_containers() -> list:
    lines = []
    lines.append("[Containers]")
    total = run(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}', '-q'])
    running = run(['docker', 'ps', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}', '-q'])
    t = len(total.split("\n")) if total else 0
    r = len(running.split("\n")) if running else 0
    lines.append(f"  Running: {r} / {t}")
    ps = run_lines(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}',
                    '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'])
    for p in ps:
        lines.append(f"  {p}")
    if len(ps) <= 1:
        fallback = run_lines(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'])
        for f in fallback:
            if 'pkb-' in f:
                lines.append(f"  {f}")
    return lines


def docker_containers_compact() -> list:
    lines = []
    lines.append("[Containers]")
    total = run(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}', '-q'])
    running = run(['docker', 'ps', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}', '-q'])
    t = len(total.split("\n")) if total else 0
    r = len(running.split("\n")) if running else 0
    lines.append(f"  Running: {r} / {t}")
    ps = run_lines(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}',
                    '--format', '{{.Names}}\t{{.Status}}'])
    for p in ps:
        if not p.startswith("pkb-"):
            continue
        name = p.split("\t")[0].replace("pkb-", "", 1)
        status = p.split("\t")[1] if "\t" in p else "?"
        if status.startswith("Up "):
            status_short = "up"
        elif status.startswith("Exited "):
            status_short = "down"
        else:
            status_short = status.split()[0] if status else "?"
        icon = "✓" if status_short == "up" else "✗"
        lines.append(f"  {icon} {name}")
    return lines


def compose_ps() -> list:
    lines = []
    lines.append("[Compose]")
    out = run_lines(['docker', 'compose', 'ps'], cwd=PROJECT_DIR)
    for o in out:
        lines.append(f"  {o}")
    return lines


def health_checks() -> list:
    lines = []
    lines.append("[Health]")
    for container in HEALTH_SERVICES:
        status = run(['docker', 'inspect', container, '--format', '{{.State.Health.Status}}'])
        name = container.replace("pkb-", "", 1)
        if status == "healthy":
            lines.append(f"  OK  {name}")
        elif status:
            lines.append(f"  --  {name} ({status})")
    return lines


def ports_info() -> list:
    lines = []
    lines.append("[Ports]")
    for port in [8080, 3300, 8082, 8081, 8083, 8084, 8086, 8087, 8090, 8091, 15432, 16379, 19001, 18092]:
        out = run(['ss', '-tlnp', f'sport = :{port}'])
        if out:
            lines.append(f"  {port}  in use")
        else:
            lines.append(f"  {port}  free")
    return lines


def volumes_info() -> list:
    lines = []
    lines.append("[Volumes]")
    vols = run_lines(['docker', 'volume', 'ls', '--filter', f'label=com.docker.compose.project={COMPOSE_PROJECT}',
                      '--format', '{{.Name}}'])
    for vol in vols:
        size = run(['docker', 'system', 'df', '-v']).split(vol)
        sz = "?"
        if len(size) > 1:
            parts = size[1].split()
            if len(parts) > 3:
                sz = parts[3]
        lines.append(f"  {vol} ({sz})")
    return lines


def logs_errors(log_lines=20) -> list:
    lines = []
    lines.append(f"[Errors] (last {log_lines} per service)")
    services = run_lines(['docker', 'compose', 'config', '--services'], cwd=PROJECT_DIR)
    if not services:
        lines.append("  (no services)")
        return lines
    found = False
    for svc in services[:10]:  # макс 10 сервисов — остальные пропускаем
        errors = run(['docker', 'compose', 'logs', '--tail=100', svc], cwd=PROJECT_DIR).split("\n")
        errs = [e for e in errors if any(x in e.lower() for x in ['error', 'traceback', 'exception', 'fail', 'critical'])]
        if errs:
            found = True
            lines.append(f"  {svc}")
            for e in errs[-log_lines:]:
                lines.append(f"    {e}")
    if not found:
        lines.append("  (no errors found)")
    return lines


# ---------------------------------------------------------------------------
# Диагностика одного сервиса
# ---------------------------------------------------------------------------

def _container_name(name: str) -> str:
    """Вернуть имя Docker-контейнера для короткого имени сервиса."""
    override = SERVICE_CONTAINERS.get(name)
    if override:
        return override
    return f"pkb-{name}"


def service_diagnostics(name: str, log_lines=20) -> list:
    container = _container_name(name)
    lines = []
    lines.append(f"[Service: {name}]")

    info = run(['docker', 'inspect', container, '--format',
                'Name: {{.Name}}\nImage: {{.Config.Image}}\nStatus: {{.State.Status}}\nHealth: {{.State.Health.Status}}\nCreated: {{.Created}}'])
    if info:
        for i in info.split("\n"):
            lines.append(f"  {i}")
    else:
        lines.append(f"  (container {container} not found)")

    stats = run(['docker', 'stats', container, '--no-stream',
                 '--format', 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'])
    for s in stats.split("\n"):
        lines.append(f"  {s}")

    lines.append(f"\n[Log errors]")
    logs = run(['docker', 'logs', container, '--tail', '100']).split("\n")
    errs = [e for e in logs if any(x in e.lower() for x in ['error', 'traceback', 'exception', 'fail', 'critical'])]
    if errs:
        for e in errs[-log_lines:]:
            lines.append(f"  {e}")
    else:
        lines.append("  (no errors)")

    lines.append(f"\n[Logs] (last {log_lines})")
    # docker logs пишет в stderr — используем shell перенаправление
    recent = run(['sh', '-c', f'docker logs {container} --tail {log_lines} 2>&1']).split("\n")
    for r in recent:
        lines.append(f"  {r}")

    return lines


# ---------------------------------------------------------------------------
# Системные логи
# ---------------------------------------------------------------------------

def system_logs(log_lines=50) -> list:
    lines = []
    lines.append("[System logs]")

    dmesg = run(['dmesg', '--level=err,warn']).split("\n")
    if dmesg:
        lines.append(f"\n[Kernel] (last {log_lines})")
        for d in dmesg[-log_lines:]:
            lines.append(f"  {d}")

    jctl = run(['journalctl', '-n', str(log_lines), '--no-pager']).split("\n")
    errors = [j for j in jctl if any(x in j.lower() for x in ['error', 'fail', 'critical', 'oom', 'killed'])]
    if errors:
        lines.append(f"\n[Journal errors] (last {log_lines})")
        for j in errors[-log_lines:]:
            lines.append(f"  {j}")

    host_proc = os.environ.get("HOST_PROC", "")
    proc_base = Path(host_proc) if host_proc else Path("/proc")

    pressure = proc_base / "pressure" / "memory"
    if pressure.exists():
        lines.append(f"\n[Memory pressure]")
        lines.append(f"  {pressure.read_text().strip()}")

    loadavg = proc_base / "loadavg"
    if loadavg.exists():
        lines.append(f"\n[Load]")
        lines.append(f"  {loadavg.read_text().strip()}")

    return lines


# ---------------------------------------------------------------------------
# Сборка ответа
# ---------------------------------------------------------------------------

def build_summary(log_lines=20, verbose=False) -> str:
    lines = []
    lines.append("=" * 52)
    lines.append("   PKB Neuroassistant — Diagnostics")
    lines.append("=" * 52)
    lines.append("")

    # System always
    for block in [system_info, health_checks]:
        lines += block()
        lines.append("")
    lines += docker_containers_compact()
    lines.append("")

    # Pipeline / Orchestrator always (live data)
    lines += orchestrator_tasks()
    lines.append("")
    lines += orchestrator_queue()
    lines.append("")

    # DB / Celery всегда
    lines += pipeline_db_info()
    lines.append("")
    lines += document_db_info()
    lines.append("")
    lines += celery_queue_info()
    lines.append("")

    lines += registry_info()
    lines.append("")

    lines += git_status_compact()
    lines.append("")

    # Verbose blocks (только ?verbose=true)
    if verbose:
        lines.append("[Extended]")
        lines.append("")
        for block in [disk_usage, docker_df, git_status,
                      docker_containers, compose_ps,
                      ports_info, volumes_info]:
            lines += block()
            lines.append("")
        lines += logs_errors(log_lines)
        lines.append("")
        lines += system_logs(50)
        lines.append("")

    lines.append("=" * 52)
    lines.append("   Diagnostics complete")
    lines.append("=" * 52)
    return "\n".join(lines)


def build_service_diagnostics(name: str, log_lines=20) -> str:
    lines = []
    lines.append("=" * 52)
    lines.append(f"   Service diagnostics: {name}")
    lines.append("=" * 52)
    lines.append("")

    lines += service_diagnostics(name, log_lines)
    lines.append("")

    # Специфичные блоки для каждого сервиса
    if name == "orchestrator":
        lines += orchestrator_tasks()
        lines.append("")
        lines += orchestrator_queue()
    elif name == "registry":
        lines += registry_info()
    elif name == "parser":
        # HTTP health + статус активных задач через parser API
        parser_health = _http_get("parser", 8087, "/api/v1/health")
        if parser_health:
            h = json.dumps(parser_health, ensure_ascii=False) if isinstance(parser_health, dict) else parser_health
            lines.append(f"[Parser HTTP health]")
            lines.append(f"  {h}")
        # Статус задач 11,12 если они активны
        for tid in [11, 12]:
            st = _http_get("orchestrator", 8081, f"/api/v1/tasks/{tid}/status")
            if st:
                lines.append(f"\n[Task #{tid} status]")
                if isinstance(st, dict):
                    for k, v in st.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"  {st}")

    lines.append("")
    lines.append("=" * 52)
    lines.append(f"   Complete: {name}")
    lines.append("=" * 52)
    return "\n".join(lines)


def build_system_logs(log_lines=100) -> str:
    lines = []
    lines.append("=" * 52)
    lines.append("   System Logs")
    lines.append("=" * 52)
    lines.append("")

    lines += system_logs(log_lines)
    lines.append("")

    lines.append("=" * 52)
    lines.append("   Complete")
    lines.append("=" * 52)
    return "\n".join(lines)
