#!/bin/bash

# Configuration for Qwen3.6-35B-A3B on i5-1240P with Iris Xe
MODEL_PATH="./Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
LLAMA_CLI="./llama.cpp/build/bin/llama-cli"

# 1. Lower swappiness to keep the 20GB model in RAM (prevents disk thrashing)
# This requires sudo. If you don't want to enter a password, you can comment this out.
if [ "$EUID" -ne 0 ]; then
    echo "Note: Running without sudo, swappiness not optimized. Run with sudo for best stability."
else
    sysctl vm.swappiness=10
fi

# 2. Run the model with optimized hardware flags
# -ngl 99: Offload all 99 layers to Iris Xe iGPU (Vulkan)
# -t 8: Use 8 threads (optimized for 4 P-cores + Hyperthreading)
# --n-cpu-moe 8: Align expert routing with the thread count
# -fa: Enable Flash Attention for memory efficiency
# -c 8192: Context window size
# -cnv: Enable conversational (chat) mode
$LLAMA_CLI \
  -m "$MODEL_PATH" \
  -ngl 99 \
  -t 8 \
  --n-cpu-moe 8 \
  -fa on \
  -c 8192 \
  --temp 0.7 \
  --repeat-penalty 1.1 \
  -p "You are an expert software engineer. Provide concise, technical answers with code examples where relevant." \
  -cnv
