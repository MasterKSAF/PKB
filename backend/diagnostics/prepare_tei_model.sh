#!/bin/bash
# =============================================================================
# Prepare TEI model (BAAI/bge-reranker-v2-m3 → ONNX int8)
#
# Скачивает модель BAAI/bge-reranker-v2-m3 и конвертирует в ONNX int8
# через optimum-cli. Результат готов для монтирования в TEI.
#
# Output: backend/models/my-bge-int8/
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODEL_DIR="$PROJECT_ROOT/backend/models/my-bge-int8"
MODEL_NAME="BAAI/bge-reranker-v2-m3"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Preparing TEI model (int8 ONNX)...${NC}"

# ── Проверка: уже готова? ───────────────────────────────────────────────────
if [ -f "$MODEL_DIR/model.onnx" ] && [ -f "$MODEL_DIR/config.json" ]; then
    echo -e "  ${GREEN}Model already prepared.${NC}"
    exit 0
fi

# ── Установка optimum ────────────────────────────────────────────────────────
if ! python3 -c "import optimum" 2>/dev/null; then
    echo "  Installing optimum[onnxruntime]..."
    pip install optimum[onnxruntime] -q 2>&1 | tail -1
fi

# ── Создание папки ───────────────────────────────────────────────────────────
mkdir -p "$MODEL_DIR"

# ── Конвертация ──────────────────────────────────────────────────────────────
echo "  Downloading $MODEL_NAME and converting to int8 ONNX..."
echo "  Output: $MODEL_DIR"
echo ""

optimum-cli export onnx \
    --model "$MODEL_NAME" \
    --optimize O2 \
    --quantize int8 \
    "$MODEL_DIR" 2>&1

if [ $? -eq 0 ] && [ -f "$MODEL_DIR/model.onnx" ]; then
    echo ""
    echo -e "  ${GREEN}Model prepared successfully.${NC}"
else
    echo ""
    echo -e "  ${RED}Model preparation failed.${NC}"
    exit 1
fi
