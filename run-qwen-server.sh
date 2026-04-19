#!/bin/bash

# Configuration for Qwen3.6-35B-A3B Server Mode
MODEL_PATH="./Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
LLAMA_SERVER="./llama.cpp/build/bin/llama-server"

# Ensure log directory exists
mkdir -p logs/slots

echo "Starting Qwen3.6-35B-A3B Server..."
echo "Logs will be streamed to stdout and saved to logs/server.log"

# Hardware optimized flags:
# -ngl 99: Full GPU offload (Iris Xe)
# -fa on: Flash Attention
# -t 8: P-Core optimized threading
# --n-cpu-moe 8: Expert routing optimization
# -v: Verbose logging
# --jinja: Use native template engine (default is enabled, but good to be explicit)
# --metrics: Enable prometheus endpoint
# --tools: Enable built-in tools for AI agents (read_file, write_file, etc.)
# --log-file: Redirect logs to file
# --log-timestamps: Include time in logs
# --log-prefix: Include prefix in logs

$LLAMA_SERVER \
  -m "$MODEL_PATH" \
  -ngl 99 \
  -fa on \
  -t 8 \
  --n-cpu-moe 8 \
  -c 16384 \
  --port 8085 \
  --host 0.0.0.0 \
  -v \
  --jinja \
  --metrics \
  --log-file logs/server.log \
  --log-timestamps \
  --log-prefix \
  --tools all \
  --slot-save-path ./logs/slots \
  2>&1 | tee logs/server_console.log
