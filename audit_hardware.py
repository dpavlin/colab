import re
import sys
from collections import Counter

def audit_hardware(file_path):
    patterns = {
        "gpu_offload": re.compile(r"offloaded (\d+)/(\d+) layers to GPU"),
        "vulkan_info": re.compile(r"Vulkan0 model buffer size = ([\d.]+) MiB"),
        "host_info": re.compile(r"CPU_Mapped model buffer size = ([\d.]+) MiB"),
        "decoding_step": re.compile(r"decoding batch, n_tokens = (\d+)"),
        "batch_timing": re.compile(r"^(\d+\.\d+\.\d+\.\d+)"),
    }

    stats = Counter()
    batch_times = []
    
    print(f"\nHARDWARE & COMPUTE DEEP-DIVE")
    print("=" * 60)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 1. Verification of GPU Configuration
                gpu_m = patterns["gpu_offload"].search(line)
                if gpu_m:
                    print(f"[CONFIGURATION] Model Layers: {gpu_m.group(1)} of {gpu_m.group(2)} on GPU")
                
                # 2. Memory Accounting
                vulk_m = patterns["vulkan_info"].search(line)
                if vulk_m:
                    print(f"[MEMORY] Vulkan VRAM Usage: {vulk_m.group(1)} MiB")
                
                host_m = patterns["host_info"].search(line)
                if host_m:
                    print(f"[MEMORY] Host RAM Usage:   {host_m.group(1)} MiB")

                # 3. Compute Spike Analysis
                batch_m = patterns["decoding_step"].search(line)
                if batch_m:
                    stats["total_batches"] += 1
                    ts_m = patterns["batch_timing"].search(line)
                    if ts_m:
                        batch_times.append(ts_m.group(1))

        print("-" * 30)
        print(f"COMPUTE THROUGHPUT:")
        print(f"  Total Batches Computed: {stats['total_batches']}")
        if len(batch_times) > 2:
            print(f"  Start of Session:       {batch_times[0]}")
            print(f"  End of Session:         {batch_times[-1]}")
        print("-" * 30)
        print("Note: Spikes in CPU/GPU correspond to 'decoding batch' events.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_hardware("logs/server.log")
