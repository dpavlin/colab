# Local Setup: Gemma 4 12B Multimodal Model

This documentation outlines the local deployment and usage of the **Gemma 4 12B Multimodal (Unified)** model on Debian/Linux using `llama.cpp` with Vulkan GPU hardware acceleration.

---

## 1. Overview
Gemma 4 12B is an "encoder-free" multimodal model that natively processes text, images, and audio directly within its decoder backbone. To run it locally without crashes, `llama.cpp` must be compiled with Vulkan backend support and invoked with the `--jinja` templating engine flag to support the custom ChatML template format.

---

## 2. Directory Structure
All components are organized in `/home/dpavlin/local-llm/`:
```text
/home/dpavlin/local-llm/
├── gemma-install.sh      # Main setup script (dependency checks, compilation, downloads)
├── gemma-tool.sh         # Bash CLI wrapper for interactive chat and file queries
├── download_gemma4.py    # Python helper script to fetch GGUFs from Hugging Face
├── GEMMA_SETUP.md        # This documentation file
├── models/
│   ├── gemma-4-12B-it-Q4_K_M.gguf      # Main text/unified model weights (7.38 GB)
│   └── mmproj-gemma-4-12B-it-Q8_0.gguf # Multimodal vision/audio projector (159 MB)
└── llama.cpp/            # Compiled local engine repository
```

---

## 3. Installation & Setup
To automate compilation and model downloads:
```bash
cd /home/dpavlin/local-llm
./gemma-install.sh
```
This script will:
1. Verify system dependencies (`cmake`, `git`, `python3`).
2. Install the `huggingface_hub` python library.
3. Clone/update `llama.cpp` and compile it with Vulkan support (`cmake -B build -DGGML_VULKAN=1`).
4. Download the GGUF models from Hugging Face if missing.
5. Set executable permissions on the tool wrapper.

---

## 4. Usage Guide (`gemma-tool.sh`)
The wrapper script simplifies invocations by auto-detecting CPU threads, defaulting to maximum Vulkan GPU offload (`-ngl 99`), and passing the required `--jinja` flag.

### A. Interactive Multimodal Chat Mode
Launch the interactive terminal chat:
```bash
./gemma-tool.sh --chat
```
Within the chat shell, you can use these commands:
*   `/image <path>` - Load a diagram or picture into the context.
*   `/audio <path>` - Load a WAV audio clip.
*   `/clear` - Wipe chat history.
*   `/exit` - Quit.

### B. Analyze an Image (Single Query)
Submit a photo directly and ask a question:
```bash
./gemma-tool.sh -i /path/to/photo.jpg "What details stand out in this photo?"
```

### C. Transcribe and Analyze Audio (Single Query)
Provide a WAV recording:
```bash
./gemma-tool.sh -a /path/to/recording.wav "Transcribe and summarize this recording."
```

### D. OpenAI-Compatible API Server
Serve the model locally:
```bash
/home/dpavlin/local-llm/llama.cpp/build/bin/llama-server \
  -m /home/dpavlin/local-llm/models/gemma-4-12B-it-Q4_K_M.gguf \
  --mmproj /home/dpavlin/local-llm/models/mmproj-gemma-4-12B-it-Q8_0.gguf \
  -ngl 99 \
  -t 16 \
  --jinja \
  --port 8080
```
You can query this server endpoint using OpenAI SDKs or standard base64 multimodal APIs.
