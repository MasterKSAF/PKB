"""
PKB Neuroassistant — Diagnostics module (встроен в Gateway)

Собирает диагностику сервера: система, Docker, Git, логи.
Работает через Docker socket (/var/run/docker.sock) и git из корня проекта.
"""

import os
import subprocess
import time
from pathlib import Path

COMPOSE_PROJECT = "pkb"
HEALTH_SERVICES = [
    "pkb-postgres", "pkb-redis", "pkb-minio", "pkb-auth",
    "pkb-registry", "pkb-parser", "pkb-converter-validator",
    "pkb-rag-builder", "pkb-rag-search", "pkb-query",
    "pkb-orchestrator", "pkb-gateway",
]
KNOWN_SERVICES = {
    "gateway", "orchestrator", "parser", "converter-validator",
    "rag-builder", "rag-search", "registry", "auth", "query",
    "postgres", "redis", "minio", "infinity",
}
START_TIME = time.time()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, timeout=30) -> str:
    """Запускает команду, возвращает stdout или пустую строку."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def run_lines(cmd, timeout=30) -> list:
    out = run(cmd, timeout)
    return out.split("\n") if out else []


# ---------------------------------------------------------------------------
# Блоки диагностики
# ---------------------------------------------------------------------------

def system_info() -> list:
    lines = []
    lines.append("[System]")
    lines.append(f"  Hostname: {run(['hostname'])}")
    lines.append(f"  Uptime:   {run(['uptime', '-p']) or run(['uptime'])}")
    lines.append(f"  Load:     {run(['uptime']).split('load average:')[-1].strip() if 'load average' in run(['uptime']) else '?'}")
    lines.append(f"  CPU:      {run(['nproc'])} cores")
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
    prj = Path(__file__).resolve().parents[2]  # проект
    prj_size = run(['du', '-sh', str(prj)])
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
    branch = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    if not branch:
        lines.append("  (not a git repository)")
        return lines
    commit = run(['git', 'rev-parse', '--short', 'HEAD'])
    msg = run(['git', 'log', '-1', '--pretty=%s'])
    lines.append(f"  Branch: {branch}")
    lines.append(f"  Commit: {commit}")
    lines.append(f"  Msg:    {msg}")
    status = run(['git', 'diff', '--stat'])
    if status:
        lines.append(f"  Dirty:  {status.split(chr(10))[-1]}")
    else:
        lines.append(f"  Dirty:  clean")
    upstream = run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}'])
    if upstream:
        upstream = upstream.replace("refs/remotes/", "")
        behind = run(['git', 'rev-list', '--count', 'HEAD..@{upstream}'])
        ahead = run(['git', 'rev-list', '--count', '@{upstream}..HEAD'])
        lines.append(f"  Remote:  {upstream}  (ahead {ahead}, behind {behind})")
    last = run_lines(['git', 'log', '--oneline', '-5'])
    for l in last:
        lines.append(f"    {l}")
    return lines


def git_status_compact() -> list:
    lines = []
    lines.append("[Git]")
    branch = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    if not branch:
        lines.append("  (not a git repository)")
        return lines
    commit = run(['git', 'rev-parse', '--short', 'HEAD'])
    lines.append(f"  Branch: {branch}")
    lines.append(f"  Commit: {commit}")
    status = run(['git', 'diff', '--stat'])
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
    out = run_lines(['docker', 'compose', 'ps'])
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
    services = run_lines(['docker', 'compose', 'config', '--services'])
    if not services:
        lines.append("  (no services)")
        return lines
    found = False
    for svc in services:
        errors = run(['docker', 'compose', 'logs', '--tail=100', svc]).split("\n")
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

def service_diagnostics(name: str, log_lines=20) -> list:
    container = f"pkb-{name}"
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
    recent = run(['docker', 'logs', container, '--tail', str(log_lines)]).split("\n")
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

    # Compact blocks (всегда)
    for block in [system_info, health_checks]:
        lines += block()
        lines.append("")

    lines += docker_containers_compact()
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
