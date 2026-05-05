#!/bin/bash
# acestep.cpp 启动脚本 (CPU 版本)
# GPU 版本编译完成后，替换为 build-cuda/

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build-cpu"
MODELS_DIR="$SCRIPT_DIR/models"
HOST="${ACE_HOST:-127.0.0.1}"
PORT="${ACE_PORT:-8085}"

echo "====================================="
echo "  acestep.cpp server"
echo "  Build: CPU"
echo "  Models: $MODELS_DIR"
echo "  Listen: $HOST:$PORT"
echo "====================================="
echo ""

# 检查模型文件
for f in \
  "vae-BF16.gguf" \
  "Qwen3-Embedding-0.6B-Q8_0.gguf" \
  "acestep-5Hz-lm-4B-Q5_K_M.gguf" \
  "acestep-v15-turbo-Q4_K_M.gguf"; do
  if [ ! -f "$MODELS_DIR/$f" ]; then
    echo "ERROR: 缺少模型文件: $f"
    exit 1
  fi
  echo "[OK] $f"
done
echo ""

# 启动服务
echo "Starting ace-server..."
"$BUILD_DIR/ace-server.exe" \
  --models "$MODELS_DIR" \
  --host "$HOST" \
  --port "$PORT" \
  --vae-chunk 128 \
  --vae-overlap 32
