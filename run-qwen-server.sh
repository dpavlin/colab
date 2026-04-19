#!/bin/bash

# Configuration for Qwen3.6-35B-A3B Server Mode
MODEL_PATH="./Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
LLAMA_SERVER="./llama.cpp/build/bin/llama-server"

# Ensure log directory exists
mkdir -p logs/slots

echo "Starting Qwen3.6-35B-A3B Server (Recurrent Caching Optimized)..."

# Optimized for Gated DeltaNet architecture:
# -c 32768: Context window
# --parallel 1: Single-user focus (Crucial for recurrent models)
# --cache-reuse 256: Proactive prefix matching
# -ctk q8_0 -ctv q8_0: Quantized cache for faster state-saving
# -ctx-checkpoints 128: More snapshots for prompt persistence
# --jinja: Native Qwen template

$LLAMA_SERVER \
  -m "$MODEL_PATH" \
  -ngl 99 \
  -fa on \
  -t 8 \
  --n-cpu-moe 8 \
  -c 32768 \
  --parallel 1 \
  --cache-reuse 256 \
  -ctk q8_0 \
  -ctv q8_0 \
  -ctx-checkpoints 128 \
  --port 8085 \
  --host 0.0.0.0 \
  -lv 4 \
  --jinja \
  --reasoning-format none \
  --metrics \
  --log-file logs/server.log \
  --log-timestamps \
  --log-prefix \
  --props \
  --slot-save-path ./logs/slots \
  2>&1 | tee logs/server_console.log
