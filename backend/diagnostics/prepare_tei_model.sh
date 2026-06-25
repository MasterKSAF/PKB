#!/bin/bash
# =============================================================================
# Prepare TEI model (BAAI/bge-reranker-v2-m3-int8)
#
# Скачивает ONNX-int8 модель и переименовывает model_quantized.onnx → model.onnx
# (необходимо для работы TEI с int8-квантованной моделью).
#
# Model: https://huggingface.co/BAAI/bge-reranker-v2-m3-int8
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODEL_DIR="$PROJECT_ROOT/models/bge-reranker-m3-int8"
MODEL_REPO="BAAI/bge-reranker-v2-m3-int8"
MODEL_URL="https://huggingface.co/$MODEL_REPO"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Preparing TEI model...${NC}"

# ── Проверка: уже скачана? ──────────────────────────────────────────────────
if [ -f "$MODEL_DIR/model.onnx" ]; then
    echo -e "  ${GREEN}Model already prepared (model.onnx found).${NC}"
    exit 0
fi

# ── Создание папки ───────────────────────────────────────────────────────────
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

# ── Проверка git-lfs ─────────────────────────────────────────────────────────
if ! command -v git-lfs &>/dev/null; then
    echo -e "  ${YELLOW}git-lfs not found, installing...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y -qq git-lfs
    git lfs install
fi

# ── Клонирование модели ──────────────────────────────────────────────────────
if [ -f "config.json" ]; then
    echo "  Model files already downloaded (config.json found)."
else
    # Определяем URL с токеном (если есть HF_TOKEN)
    CLONE_URL="$MODEL_URL"
    if [ -n "${HF_TOKEN:-}" ]; then
        CLONE_URL="https://user:${HF_TOKEN}@huggingface.co/$MODEL_REPO"
    fi

    echo "  Downloading model from $MODEL_REPO ..."
    GIT_LFS_SKIP_SMUDGE=0 git clone --depth 1 "$CLONE_URL" . 2>&1 || {
        echo -e "  ${RED}Failed to download model.${NC}"
        echo "  Try: export HF_TOKEN=your_token && $0"
        exit 1
    }
fi

# ── Переименование model_quantized.onnx → model.onnx ────────────────────────
if [ -f "model_quantized.onnx" ] && [ ! -f "model.onnx" ]; then
    echo "  Renaming model_quantized.onnx → model.onnx ..."
    mv model_quantized.onnx model.onnx
    echo -e "  ${GREEN}Done.${NC}"
elif [ -f "model.onnx" ]; then
    echo -e "  ${GREEN}model.onnx already exists.${NC}"
else
    echo -e "  ${RED}model_quantized.onnx not found in $MODEL_DIR${NC}"
    echo "  Check model files: ls -la $MODEL_DIR"
    exit 1
fi

echo -e "${GREEN}TEI model prepared: $MODEL_DIR${NC}"
