#!/usr/bin/env bash

# gemma-install.sh - Install and compile setup script for Gemma 4 12B Multimodal model

set -euo pipefail

# Base Configs
BASE_DIR="/home/dpavlin/local-llm"
LLAMA_DIR="${BASE_DIR}/llama.cpp"
MODEL_DIR="${BASE_DIR}/models"
DOWNLOAD_SCRIPT="${BASE_DIR}/download_gemma4.py"
TOOL_SCRIPT="${BASE_DIR}/gemma-tool.sh"

debug_log() {
    echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# 1. Dependency Checks
debug_log "Checking dependencies..."

missing_deps=()
for cmd in cmake git python3; do
    if ! command -v "$cmd" &>/dev/null; then
        missing_deps+=("$cmd")
    fi
done

if [[ ${#missing_deps[@]} -ne 0 ]]; then
    echo "Error: Missing core system dependencies: ${missing_deps[*]}" >&2
    echo "Please install them via apt-get: sudo apt-get install -y cmake git python3-pip" >&2
    exit 1
fi

# Check huggingface_hub python package
if ! python3 -c "import huggingface_hub" &>/dev/null; then
    debug_log "huggingface_hub python library not found. Installing..."
    python3 -m pip install --user huggingface_hub
fi

# 2. Check and Setup llama.cpp
if [[ ! -d "$LLAMA_DIR" ]]; then
    debug_log "llama.cpp repository not found. Cloning latest master..."
    git clone https://github.com/ggml-org/llama.cpp.git "$LLAMA_DIR"
else
    debug_log "llama.cpp repository found. Updating to latest remote..."
    (cd "$LLAMA_DIR" && git checkout master && git pull)
fi

# 3. Compile llama.cpp with Vulkan GPU support
debug_log "Configuring and building llama.cpp with Vulkan..."
cd "$LLAMA_DIR"
cmake -B build -DGGML_VULKAN=1
cmake --build build --config Release -j"$(nproc)"

# Verify the CLI tool compiled
MTMD_CLI="${LLAMA_DIR}/build/bin/llama-mtmd-cli"
if [[ ! -f "$MTMD_CLI" ]]; then
    echo "Error: llama-mtmd-cli binary was not built successfully at $MTMD_CLI" >&2
    exit 1
fi
debug_log "llama-mtmd-cli compiled successfully."

# 4. Download / Verify Gemma 4 Models
cd "$BASE_DIR"
if [[ -f "$DOWNLOAD_SCRIPT" ]]; then
    debug_log "Downloading/verifying Gemma 4 12B GGUF models..."
    python3 "$DOWNLOAD_SCRIPT"
else
    echo "Error: Missing download helper script at $DOWNLOAD_SCRIPT" >&2
    exit 1
fi

# 5. Make gemma-tool.sh executable
if [[ -f "$TOOL_SCRIPT" ]]; then
    debug_log "Setting executable permissions on gemma-tool.sh..."
    chmod +x "$TOOL_SCRIPT"
else
    echo "Warning: gemma-tool.sh wrapper script not found at $TOOL_SCRIPT" >&2
fi

debug_log "Installation and compilation setup finished successfully!"
echo "------------------------------------------------------------------"
echo " You can now run the model using the wrapper tool:"
echo "   ./gemma-tool.sh --chat"
echo "------------------------------------------------------------------"
