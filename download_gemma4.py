import os
import sys
from huggingface_hub import hf_hub_download

repo_id = "ggml-org/gemma-4-12B-it-GGUF"
local_dir = "/home/dpavlin/local-llm/models"

os.makedirs(local_dir, exist_ok=True)

files_to_download = [
    "gemma-4-12B-it-Q4_K_M.gguf",
    "mmproj-gemma-4-12B-it-Q8_0.gguf"
]

print(f"[DEBUG] Hugging Face Repo: {repo_id}")
print(f"[DEBUG] Target Directory: {local_dir}")

for filename in files_to_download:
    dest_path = os.path.join(local_dir, filename)
    if os.path.exists(dest_path):
        print(f"[DEBUG] File already exists at {dest_path}. Skipping download.")
        continue
    
    print(f"[DEBUG] Downloading {filename} to {dest_path}...")
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        print(f"[DEBUG] Successfully downloaded to {path}")
    except Exception as e:
        print(f"[ERROR] Failed to download {filename}: {e}", file=sys.stderr)
        sys.exit(1)

print("[DEBUG] Download process completed successfully.")
