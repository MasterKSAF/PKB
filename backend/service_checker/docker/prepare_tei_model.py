#!/usr/bin/env python3
"""
PKB Neuroassistant — Prepare TEI model locally.

Скачивает конфигурационные файлы из cointegrated/rubert-tiny2
и ONNX-файл из TrendHD/rubert-tiny2-int8, переименовывает его
в model.onnx, чтобы TEI мог загрузить модель из локальной папки.

Структура на выходе:
  docker/tei_model/
  ├── config.json
  ├── tokenizer.json
  ├── tokenizer_config.json
  ├── special_tokens_map.json
  ├── vocab.txt
  └── model.onnx             (переименованный rubert-tiny2-int8.onnx)
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

# Модели для конфигов и ONNX-весов
CONFIG_REPO = "cointegrated/rubert-tiny2"
ONNX_REPO = "TrendHD/rubert-tiny2-int8"

CONFIG_FILES = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.txt",
]

ONNX_SOURCE = "onnx/rubert-tiny2-int8.onnx"
ONNX_TARGET = "model.onnx"

REQUIRED_FILES = [*CONFIG_FILES, ONNX_TARGET]
MIN_ONNX_BYTES = 1024


def _is_ready_file(path: Path, min_size: int = 1) -> bool:
    """Файл существует, не symlink и не пустой."""
    try:
        return path.is_file() and path.stat().st_size >= min_size
    except OSError:
        return False


def _remove_broken(path: Path) -> None:
    """Удалить битую symlink или пустой файл."""
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or not _is_ready_file(path):
        path.unlink(missing_ok=True)


def _download_config(target: Path, filename: str) -> None:
    dest = target / filename
    if _is_ready_file(dest):
        print(f"  ✓ {filename} already exists, skipping")
        return

    _remove_broken(dest)
    print(f"  → {filename}...", end=" ", flush=True)
    try:
        hf_hub_download(
            repo_id=CONFIG_REPO,
            filename=filename,
            local_dir=str(target),
        )
        resolved = dest.resolve()
        if not _is_ready_file(resolved):
            raise OSError(f"downloaded file is missing or empty: {dest}")
        if resolved != dest.resolve():
            shutil.copy2(resolved, dest)
        print("OK")
    except Exception as exc:
        print(f"FAILED: {exc}")
        raise


def _download_onnx(target: Path) -> None:
    dest_onnx = target / ONNX_TARGET
    if _is_ready_file(dest_onnx, min_size=MIN_ONNX_BYTES):
        print(f"\n  ✓ {ONNX_TARGET} already exists, skipping")
        return

    _remove_broken(dest_onnx)
    print(f"\nDownloading ONNX model: {ONNX_SOURCE}...", end=" ", flush=True)
    try:
        downloaded = hf_hub_download(
            repo_id=ONNX_REPO,
            filename=ONNX_SOURCE,
            local_dir=str(target),
        )
        src = Path(downloaded)
        if not _is_ready_file(src, min_size=MIN_ONNX_BYTES):
            src = target / ONNX_SOURCE
        if not _is_ready_file(src, min_size=MIN_ONNX_BYTES):
            raise OSError(f"ONNX file is missing or too small: {src}")

        shutil.copy2(src, dest_onnx)
        if not _is_ready_file(dest_onnx, min_size=MIN_ONNX_BYTES):
            raise OSError(f"failed to materialize {ONNX_TARGET}")

        onnx_subdir = target / "onnx"
        if onnx_subdir.is_dir():
            shutil.rmtree(onnx_subdir, ignore_errors=True)

        print("OK")
        print(f"  → Saved as {ONNX_TARGET}")
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)


def _print_structure(target: Path) -> None:
    print("\nFinal model structure:")
    missing: list[str] = []
    for name in REQUIRED_FILES:
        path = target / name
        if _is_ready_file(path, min_size=MIN_ONNX_BYTES if name == ONNX_TARGET else 1):
            size = path.stat().st_size
            print(f"  {name:30s} {size // 1024:>6} KB")
        else:
            print(f"  {name:30s} MISSING")
            missing.append(name)

    if missing:
        print(f"\n✗ Missing files: {', '.join(missing)}")
        sys.exit(1)


def prepare_model(target_dir: str | None = None) -> None:
    """Скачать и подготовить модель для TEI.

    Args:
        target_dir: Путь к директории для модели.
            По умолчанию: docker/tei_model/ относительно директории скрипта.
    """
    if target_dir is None:
        script_dir = Path(__file__).resolve().parent
        target_dir = str(script_dir / "tei_model")

    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    print(f"Preparing TEI model in: {target}")

    print("\nDownloading config files...")
    for filename in CONFIG_FILES:
        _download_config(target, filename)

    _download_onnx(target)
    _print_structure(target)

    print(f"\n✓ Model prepared at: {target}")
    print("  Mount this directory as /data in TEI container and run with --model-id /data")


if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else None
    prepare_model(target_arg)
