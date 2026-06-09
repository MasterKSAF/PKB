#!/usr/bin/env python3
"""
PKB Neuroassistant — Prepare TEI model locally.

Скачивает конфигурационные файлы из cointegrated/rubert-tiny2
и ONNX-файл из TrendHD/rubert-tiny2-int8, переименовывает его
в model_quantized.onnx, чтобы TEI мог загрузить модель из локальной папки.

Структура на выходе:
  tei_model/
  ├── config.json
  ├── tokenizer.json
  ├── tokenizer_config.json
  ├── special_tokens_map.json
  ├── vocab.txt
  └── model_quantized.onnx   (переименованный rubert-tiny2-int8.onnx)
"""

from __future__ import annotations

import os
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
ONNX_TARGET = "model_quantized.onnx"


def prepare_model(target_dir: str = "tei_model") -> None:
    """Скачать и подготовить модель для TEI."""
    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    print(f"Preparing TEI model in: {target}")

    # 1. Скачиваем конфигурационные файлы
    print("\nDownloading config files...")
    for filename in CONFIG_FILES:
        dest = target / filename
        if dest.exists():
            print(f"  ✓ {filename} already exists, skipping")
            continue
        print(f"  → {filename}...", end=" ", flush=True)
        try:
            hf_hub_download(
                repo_id=CONFIG_REPO,
                filename=filename,
                local_dir=str(target),
                local_dir_use_symlinks=False,
            )
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")

    # 2. Скачиваем ONNX-файл и переименовываем
    dest_onnx = target / ONNX_TARGET
    if dest_onnx.exists():
        print(f"\n  ✓ {ONNX_TARGET} already exists, skipping")
    else:
        print(f"\nDownloading ONNX model: {ONNX_SOURCE}...", end=" ", flush=True)
        try:
            downloaded = hf_hub_download(
                repo_id=ONNX_REPO,
                filename=ONNX_SOURCE,
                local_dir_use_symlinks=False,
            )
            # Переименовываем в ожидаемое TEI имя (shutil.move для кроссплатформенности)
            import shutil
            shutil.move(downloaded, str(dest_onnx))
            print("OK")
            print(f"  → Renamed to {ONNX_TARGET}")
        except Exception as e:
            print(f"FAILED: {e}")
            sys.exit(1)

    # 3. Проверяем структуру
    print("\nFinal model structure:")
    for f in sorted(target.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:30s} {size//1024:>6} KB")

    print(f"\n✓ Model prepared at: {target}")
    print("  Mount this directory as /data in TEI container and run with --model-id /data")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "tei_model"
    prepare_model(target)
