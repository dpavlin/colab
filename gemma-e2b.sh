#!/usr/bin/env bash

# gemma-e2b.sh - Wrapper for Gemma 4 E2B (2.3B) Multimodal model using llama.cpp
# Usage: ./gemma-e2b.sh [options] [prompt]

set -euo pipefail

# Base Paths
BASE_DIR="/home/dpavlin/local-llm"
MMPROJ_PATH="${BASE_DIR}/models/e2b/mmproj-F16.gguf"
CLI_PATH="${BASE_DIR}/llama.cpp/build/bin/llama-mtmd-cli"

# Default Model (Q4)
MODEL_PATH="${BASE_DIR}/models/e2b/gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf"

# Default settings
GPU_LAYERS=99
THREADS=$(nproc || echo 8)
IMAGE=""
AUDIO=""
PROMPT=""
CHAT_MODE=false

debug_log() {
    echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

show_help() {
    cat << EOF
Usage: $0 [options] [prompt]

Options:
  -i, --image FILE      Path to input image
  -a, --audio FILE      Path to input WAV audio file
  -p, --prompt STRING   Text prompt/query (defaults to gas meter OCR if image is provided)
  -c, --chat            Force interactive chat mode (ignores -p)
  --q2                  Use Q2 quantization model (gemma-4-E2B-it-qat-UD-Q2_K_XL.gguf)
  --q4                  Use Q4 quantization model (gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf) [default]
  -g, --gpu N           Number of GPU layers to offload (default: $GPU_LAYERS)
  -t, --threads N       Number of CPU threads to use (default: $THREADS)
  -h, --help            Show this help message

Examples:
  $0 -i gas_meter.jpg
  $0 -i photo.jpg "What details stand out?"
  $0 --chat
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--image)
            IMAGE="$2"
            shift 2
            ;;
        -a|--audio)
            AUDIO="$2"
            shift 2
            ;;
        -p|--prompt)
            PROMPT="$2"
            shift 2
            ;;
        -c|--chat)
            CHAT_MODE=true
            shift
            ;;
        --q2)
            MODEL_PATH="${BASE_DIR}/models/e2b/gemma-4-E2B-it-qat-UD-Q2_K_XL.gguf"
            shift
            ;;
        --q4)
            MODEL_PATH="${BASE_DIR}/models/e2b/gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf"
            shift
            ;;
        -g|--gpu)
            GPU_LAYERS="$2"
            shift 2
            ;;
        -t|--threads)
            THREADS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [[ -z "$PROMPT" ]]; then
                PROMPT="$1"
                shift
            else
                echo "Unknown argument: $1" >&2
                show_help
                exit 1
            fi
            ;;
    esac
done

# Verify core dependencies
for f in "$MODEL_PATH" "$MMPROJ_PATH" "$CLI_PATH"; do
    if [[ ! -f "$f" ]]; then
        echo "Error: Required file not found at $f" >&2
        exit 1
    fi
done

# Build command arguments
CMD=("$CLI_PATH" "-m" "$MODEL_PATH" "--mmproj" "$MMPROJ_PATH" "-ngl" "$GPU_LAYERS" "-t" "$THREADS" "--jinja")

# Handle input validation
if [[ -n "$IMAGE" ]]; then
    if [[ ! -f "$IMAGE" ]]; then
        echo "Error: Image file not found at $IMAGE" >&2
        exit 1
    fi
    CMD+=("--image" "$IMAGE")
fi

if [[ -n "$AUDIO" ]]; then
    if [[ ! -f "$AUDIO" ]]; then
        echo "Error: Audio file not found at $AUDIO" >&2
        exit 1
    fi
    CMD+=("--audio" "$AUDIO")
fi

# Route mode based on args
if [ "$CHAT_MODE" = true ] || [[ -z "$PROMPT" && -z "$IMAGE" && -z "$AUDIO" ]]; then
    debug_log "Starting interactive chat mode using model: $(basename "$MODEL_PATH")"
    exec "${CMD[@]}"
else
    # Default gas meter prompt if an image is provided but no prompt is explicitly set
    if [[ -n "$IMAGE" && -z "$PROMPT" ]]; then
        PROMPT="This image shows a gas meter with a horizontal sequence of digits in separate slots. The digits representing the whole number of cubic meters have a black/dark background, while the decimal digits on the right have a red background. A small pointer/indicator marks the decimal comma. Please transcribe only the digits with the black/dark background (the ones before the decimal pointer representing whole cubic meters)."
    elif [[ -z "$PROMPT" ]]; then
        PROMPT="Describe what you see or hear."
    fi
    debug_log "Running query using model $(basename "$MODEL_PATH"): '$PROMPT'"
    exec "${CMD[@]}" -p "$PROMPT"
fi
