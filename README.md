# Fine-Tuning LLM on Intel Laptop: Lessons & Lifecycle

This project explored the feasibility of fine-tuning a Large Language Model (LLM) on a 12th Gen Intel Laptop to learn from personal CLI interactions and Git history.

## 1. Hardware Analysis (Intel i5-1240P)
- **CPU:** 12th Gen Intel Core i5-1240P (12 cores, 16 threads).
- **GPU:** Intel Iris Xe (Alder Lake-P).
- **RAM:** 32GB (Crucial for running 7B-14B models locally).
- **Conclusion:** While local inference is excellent, local training is extremely slow on CPU. The optimal path is **Cloud Training (Colab/Kaggle) -> Local Inference (Ollama/llama.cpp)**.

## 2. Data Extraction Strategy
We developed a parallelized extraction pipeline to transform Gemini CLI history into high-fidelity training data.
- **Source:** `~/.gemini/tmp/`
- **Formats Processed:**
    - `logs.json`: Simple instruction-response pairs.
    - `checkpoint-*.json`: Multi-turn conversation snapshots.
    - `session-*.json`: Full agent traces including `<thought>` blocks and `[TOOL_CALL]` / `[TOOL_RESULT]` chains.
- **Privacy:** Implemented a regex-based **Secret Scrubber** to redact API keys, passwords, and WiFi credentials.
- **Result:** Successfully converted ~500 files into a **73,000-turn** ShareGPT-formatted dataset (`sharegpt_training_data.jsonl`).

## 3. Training & Quantization
- **Model Choice:** Qwen-2.5-7B (Optimized for coding and agentic tasks).
- **Platform:** Google Colab (Tesla T4 GPU) using the **Unsloth** library for 2x faster training.
- **Format:** Exported as **GGUF (Q4_K_M)** for maximum efficiency on Intel hardware.

## 4. Local Deployment & Findings
- **Runner:** Developed a Python-based **Agent Runner** to bridge the model's `[TOOL_CALL]` outputs with local execution (`list_directory`, `read_file`, `run_shell_command`).
- **GPU Issues:** 
    - Official Ollama (v0.17.x) Vulkan backend caused corrupted "gibberish" output on Intel Iris Xe.
    - CPU-only mode was stable and reliable for the 7B model given the 32GB of RAM.
- **Memory Fix:** Discovered that the standard Ollama `Modelfile` template needs a specific `{{- range .Messages }}` loop to support multi-turn agent logic.

## 5. Cleanup
A full system cleanup was performed to remove experimental environments, though the extraction logic and lessons remain preserved in this documentation.

---
*Date: March 12, 2026*
