# Local Qwen 3.6-35B-A3B Setup (NUC Optimized)

This document describes the optimized setup for running the **Qwen3.6-35B-A3B** model on an Intel i5-1240P (12th Gen) laptop with 32GB RAM and Iris Xe Graphics using `llama.cpp` and `opencode`.

## Hardware Specifications
- **CPU:** Intel Core i5-1240P (4P + 8E cores)
- **RAM:** 32GB (DDR4/DDR5)
- **GPU:** Intel Iris Xe Graphics (80 EUs)
- **Backend:** `llama.cpp` with Vulkan acceleration

## Model Details
- **Model:** Qwen3.6-35B-A3B
- **Format:** GGUF (UD-Q4_K_M quantization)
- **Size:** ~20.6 GiB
- **Active Parameters:** 3 Billion (MoE)

## Optimization Strategy
1. **GPU Offloading:** 100% of layers offloaded to Iris Xe iGPU via Vulkan for fast prompt processing (~38 t/s).
2. **CPU Threading:** Pinned to 8 threads to utilize Performance cores efficiently while avoiding Efficiency core bottlenecks.
3. **Memory Management:** `swappiness` lowered to 10 to keep the 20GB model strictly in RAM.
4. **Agentic Layer:** Integrated with `opencode` via an OpenAI-compatible API on port 8085.

## Available Scripts

### 1. `run-qwen.sh`
Interactive CLI mode. Use this for standard chat directly in the terminal.
```bash
./run-qwen.sh
```

### 2. `run-qwen-server.sh`
Starts the `llama-server` on port 8085 with high verbosity and experimental tool support.
```bash
./run-qwen-server.sh
```

## Agentic Integration (opencode)
The model is configured as a provider in `opencode` under the name `nuc-qwen36`.

To start an agentic session with tool access (file reading, shell execution, etc.):
```bash
opencode run -m nuc-qwen36/qwen3.6-35B-A3B "Your prompt here"
```

## Prompt Caching & Persistence

To avoid the 5-8 minute prefill delay for large prompts (like the 10k token opencode system prompt), you can persist the model's "recurrent state" to disk.

### 1. Automatic Prompt Caching
The server is configured to proactively reuse prefix chunks via `--cache-reuse 256`. To force a permanent disk cache for a static system prompt, you can add these flags to the start script:
```bash
--prompt-cache logs/system_cache.bin --prompt-cache-all
```

### 2. Manual Session Persistence (Recommended for opencode)
You can save and restore the exact state of a conversation slot (e.g., Slot 0) using the REST API. This is nearly instant.

**To Save a Session:**
```bash
curl -X POST http://localhost:8085/slots/0?action=save \
  -H "Content-Type: application/json" \
  -d '{"filename": "opencode_session.bin"}'
```

**To Restore a Session:**
```bash
curl -X POST http://localhost:8085/slots/0?action=restore \
  -H "Content-Type: application/json" \
  -d '{"filename": "opencode_session.bin"}'
```

*Note: Files are saved in the directory specified by `--slot-save-path` (default: `logs/slots/`).*

### 3. Critical Compatibility Rules
- **Large Files:** For Qwen 3.6 (DeltaNet), these cache files can be 100MB - 500MB+ per slot.
- **Strict Matching:** A saved cache can ONLY be restored if the model file, `--ctx-size`, and `--parallel` count are identical to when it was saved.

## Maintenance
- **Logs:** Server logs are stored in `logs/server.log`.
- **KV Cache:** Slot states are saved in `logs/slots/` for improved session continuity.
