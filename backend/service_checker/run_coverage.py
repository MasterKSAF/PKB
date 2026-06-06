#!/usr/bin/env python3
"""
Запуск мок-сервисов и API Coverage Test в одном процессе.
"""
import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GATEWAY_DIR = PROJECT_ROOT / "backend" / "gateway_service"
PYTHON = sys.executable

MOCKS = [
    ("auth", 8082, "mocks.auth_service.main:app"),
    ("orchestrator", 8081, "mocks.orchestrator_service.main:app"),
    ("query", 8083, "mocks.query_service.main:app"),
    ("registry", 8084, "mocks.registry_service.main:app"),
]


async def start_mocks():
    """Запустить мок-сервисы."""
    processes = []
    for name, port, app in MOCKS:
        proc = await asyncio.create_subprocess_exec(
            PYTHON, "-m", "uvicorn", app,
            "--host", "127.0.0.1", "--port", str(port),
            cwd=str(GATEWAY_DIR),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        processes.append((name, port, proc))
        print(f"  🚀 {name}:{port} started (PID {proc.pid})")
    return processes


async def wait_for_mocks(processes, timeout=15):
    """Дождаться пока все моки начнут отвечать."""
    import httpx

    async def wait_one(name, port):
        client = httpx.AsyncClient(timeout=3)
        try:
            for attempt in range(timeout):
                try:
                    r = await client.get(f"http://127.0.0.1:{port}/api/v1/system/health")
                    if r.status_code < 500:
                        return True
                except Exception:
                    pass
                await asyncio.sleep(1)
            return False
        finally:
            await client.aclose()

    results = await asyncio.gather(*[wait_one(name, port) for name, port, _ in processes])
    all_ok = True
    for (name, port, _), ok in zip(processes, results):
        status = "✅" if ok else "❌"
        print(f"  {status} {name}:{port}")
        if not ok:
            all_ok = False
    return all_ok


async def run_coverage_test(output_path=None, mode: str = "mock"):
    """Импортировать и запустить тест покрытия."""
    # Добавляем service_checker в путь
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from service_checker.api_coverage_test import ApiCoverageTester

    tester = ApiCoverageTester(mode=mode, base_host="127.0.0.1")
    try:
        await tester.run_all()
        report = tester.generate_report()

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"\n  📄 Report saved: {out.resolve()}")
        else:
            from datetime import datetime
            auto_name = f"api_coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            auto_path = Path(auto_name)
            auto_path.write_text(report, encoding="utf-8")
            print(f"\n  📄 Report saved: {auto_path.resolve()}")
    finally:
        await tester.close()


async def stop_mocks(processes):
    """Остановить моки."""
    print("\n  🛑 Stopping mocks...")
    for name, port, proc in processes:
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5)
            print(f"  ✋ {name}:{port} stopped")
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


async def main():
    args = sys.argv[1:]
    output = "api_coverage_report.md"
    mode = "mock"

    # Парсим --mode и -o вручную без argparse
    for i, arg in enumerate(args):
        if arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
        elif arg == "-o" and i + 1 < len(args):
            output = args[i + 1]

    mode_label = {"mock": "🧪 Mock", "real": "🔬 Real"}
    print("=" * 60)
    print(f"  PKB Neuroassistant — API Coverage Test Runner")
    print(f"  {mode_label.get(mode, mode)}")
    print("=" * 60)

    if mode == "mock":
        print("\n  Starting mock services...")
        processes = await start_mocks()
        print("\n  Waiting for mocks to be ready...")
        ok = await wait_for_mocks(processes)

        if not ok:
            print("\n  ⚠️  Some mocks not ready, continuing anyway...")
        else:
            print("\n  ✅ All mocks ready!")
    else:
        print("\n  🔍 Real mode — не запускаем сервисы, используем уже запущенные")
        processes = []

    print("\n" + "─" * 60)
    print("  Running API Coverage Test...")
    print("─" * 60 + "\n")

    try:
        await run_coverage_test(output, mode=mode)
    finally:
        if processes:
            await stop_mocks(processes)

    print("\n  ✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
