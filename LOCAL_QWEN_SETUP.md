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

## Maintenance
- **Logs:** Server logs are stored in `logs/server.log`.
- **KV Cache:** Slot states are saved in `logs/slots/` for improved session continuity.
