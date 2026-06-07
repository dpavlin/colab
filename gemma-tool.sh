#!/usr/bin/env bash

# gemma-tool.sh - Wrapper for Gemma 4 12B Multimodal model using llama.cpp
# Usage: ./gemma-tool.sh [options] [prompt]

set -euo pipefail

# Base Paths
BASE_DIR="/home/dpavlin/local-llm"
MODEL_PATH="${BASE_DIR}/models/gemma-4-12B-it-Q4_K_M.gguf"
MMPROJ_PATH="${BASE_DIR}/models/mmproj-gemma-4-12B-it-Q8_0.gguf"
CLI_PATH="${BASE_DIR}/llama.cpp/build/bin/llama-mtmd-cli"

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
  -p, --prompt STRING   Text prompt/query (defaults to interactive chat mode if prompt/query is omitted)
  -c, --chat            Force interactive chat mode (ignores -p)
  -g, --gpu N           Number of GPU layers to offload (default: $GPU_LAYERS)
  -t, --threads N       Number of CPU threads to use (default: $THREADS)
  -h, --help            Show this help message

Examples:
  $0 -i photo.jpg "Describe this photo"
  $0 -a recording.wav "Summarize this recording"
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
            # Map positional argument to prompt if prompt is empty
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
    debug_log "Starting interactive chat mode..."
    exec "${CMD[@]}"
else
    if [[ -z "$PROMPT" ]]; then
        PROMPT="Describe what you see or hear."
    fi
    debug_log "Running single-prompt query: '$PROMPT'"
    exec "${CMD[@]}" -p "$PROMPT"
fi
