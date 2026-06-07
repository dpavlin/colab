# Local Setup: NVIDIA Nemotron 3.5 ASR with Vulkan GPU Acceleration

This documentation outlines the local deployment, compilation, and usage of NVIDIA's **Nemotron 3.5 ASR (0.6B)** Automatic Speech Recognition model on Debian/Linux using **`parakeet.cpp`** and Vulkan GPU hardware acceleration.

---

## 1. Overview
Nemotron 3.5 ASR is a cache-aware streaming speech-recognition model. Using **`parakeet.cpp`** (a lightweight C++ implementation built on the `ggml` tensor engine), you can run this model locally with hardware acceleration on your Intel Integrated GPU (via Vulkan/Mesa drivers) without requiring Python or PyTorch runtimes.

---

## 2. Directory Structure
All components are integrated in `/home/dpavlin/local-llm/`:
```text
/home/dpavlin/local-llm/
├── dictate-nemotron.sh   # Dictation script (recording -> parakeet-cli ASR -> paste)
├── NEMOTRON_ASR_SETUP.md # This documentation file
├── models/
│   └── nemotron-3.5-asr-streaming-0.6b-q4_k.gguf # Quantized ASR weights (718 MB)
└── parakeet.cpp/         # Compiled local C++ ASR engine repository (ignored in git)
    └── build/examples/cli/parakeet-cli  # Compiled engine binary
```

---

## 3. Installation & Compilation Setup

### A. Dependencies
Ensure you have the required Vulkan development tools and Mesa drivers installed:
```bash
sudo apt-get install -y cmake git mesa-vulkan-drivers vulkan-tools ffmpeg xdotool xclip
```

### B. Checkout and Compile `parakeet.cpp`
Clone the engine repository recursively and compile it with the Vulkan backend enabled:
```bash
cd /home/dpavlin/local-llm
git clone --recursive https://github.com/mudler/parakeet.cpp.git
cd parakeet.cpp
cmake -B build -DPARAKEET_GGML_VULKAN=ON
cmake --build build --config Release -j$(nproc)
```
This builds the `parakeet-cli` executable under `build/examples/cli/`.

### C. Download the GGUF Model
Download the quantized streaming model directly from the Hugging Face repository `mudler/parakeet-cpp-gguf` into your local models directory:
```python
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id="mudler/parakeet-cpp-gguf",
    filename="nemotron-3.5-asr-streaming-0.6b-q4_k.gguf",
    local_dir="/home/dpavlin/local-llm/models"
)
```

---

## 4. Usage Guide

### A. Transcribe WAV File via CLI (`parakeet-cli`)
To transcribe a pre-recorded 16kHz mono WAV file using your Intel iGPU:
```bash
/home/dpavlin/local-llm/parakeet.cpp/build/examples/cli/parakeet-cli transcribe \
  --model /home/dpavlin/local-llm/models/nemotron-3.5-asr-streaming-0.6b-q4_k.gguf \
  --input /path/to/audio.wav
```

You can optionally append the `--stream` flag to simulate streaming/incremental chunk-based transcription:
```bash
/home/dpavlin/local-llm/parakeet.cpp/build/examples/cli/parakeet-cli transcribe \
  --model /home/dpavlin/local-llm/models/nemotron-3.5-asr-streaming-0.6b-q4_k.gguf \
  --input /path/to/audio.wav \
  --stream
```

### B. Desktop Dictation Setup (`dictate-nemotron.sh`)
The `dictate-nemotron.sh` script automates recording from your microphone, performing local GPU-accelerated transcription, and typing it into the currently active window.

#### 1. Interactive terminal usage:
```bash
/home/dpavlin/local-llm/dictate-nemotron.sh
```
Press **[Enter]** to stop recording, transcribe, and copy/paste.

#### 2. Global Hotkey / Toggle integration:
Bind your desktop environment shortcut to run the script with the toggle argument:
```bash
/home/dpavlin/local-llm/dictate-nemotron.sh --toggle
```
* **First Trigger:** Starts microphone recording in the background (accompanied by sound chime and desktop notification).
* **Second Trigger:** Stops recording, pushes PCM frames to Vulkan GPU, strips language tags, copies to clipboard, and simulates keystrokes to paste the text instantly.
