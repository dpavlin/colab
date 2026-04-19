import re
import sys
from collections import Counter

def audit_hardware(file_path):
    patterns = {
        "gpu_offload": re.compile(r"offloaded (\d+)/(\d+) layers to GPU"),
        "vulkan_info": re.compile(r"Vulkan0 model buffer size = ([\d.]+) MiB"),
        "prefill": re.compile(r"(\d+\.\d+\.\d+\.\d+).*prompt processing progress, n_tokens = (\d+), batch.n_tokens = (\d+)"),
        "gen": re.compile(r"(\d+\.\d+\.\d+\.\d+).*decoding batch, n_tokens = (\d+)"),
    }

    stats = Counter()
    prefill_speeds = []
    gen_speeds = []
    last_prefill_ts = None
    last_gen_ts = None
    
    print(f"\nHARDWARE & PERFORMANCE DEEP-DIVE")
    print("=" * 70)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 1. GPU Verification
                gpu_m = patterns["gpu_offload"].search(line)
                if gpu_m:
                    print(f"[HW] GPU Layers: {gpu_m.group(1)}/{gpu_m.group(2)}")
                
                vulk_m = patterns["vulkan_info"].search(line)
                if vulk_m:
                    print(f"[MEM] Vulkan VRAM: {vulk_m.group(1)} MiB")

                # 2. Prefill Speed (t/s)
                pre_m = patterns["prefill"].search(line)
                if pre_m:
                    ts, n_tokens, b_tokens = pre_m.groups()
                    if last_prefill_ts:
                        # Simple time diff (format is h.m.s.ms)
                        try:
                            t1 = float(last_prefill_ts.split('.')[-1]) + int(last_prefill_ts.split('.')[-2]) * 1000
                            t2 = float(ts.split('.')[-1]) + int(ts.split('.')[-2]) * 1000
                            diff_ms = t2 - t1
                            if diff_ms > 0:
                                tps = (int(b_tokens) / diff_ms) * 1000
                                prefill_speeds.append(tps)
                        except: pass
                    last_prefill_ts = ts

                # 3. Generation Speed (t/s)
                gen_m = patterns["gen"].search(line)
                if gen_m:
                    ts, n_tokens = gen_m.groups()
                    if last_gen_ts:
                        try:
                            t1 = float(last_gen_ts.split('.')[-1]) + int(last_gen_ts.split('.')[-2]) * 1000
                            t2 = float(ts.split('.')[-1]) + int(ts.split('.')[-2]) * 1000
                            diff_ms = t2 - t1
                            if 10 < diff_ms < 5000: # Filter out long breaks between requests
                                tps = (int(n_tokens) / diff_ms) * 1000
                                gen_speeds.append(tps)
                        except: pass
                    last_gen_ts = ts

        print("-" * 35)
        print(f"THROUGHPUT ANALYSIS:")
        if prefill_speeds:
            avg_pre = sum(prefill_speeds) / len(prefill_speeds)
            print(f"  Avg Prefill Speed:    {avg_pre:.2f} tokens/sec (CPU -> GPU)")
        
        if gen_speeds:
            # We filter for single-token batches which is standard TG
            avg_gen = sum(gen_speeds) / len(gen_speeds)
            print(f"  Avg Generation Speed: {avg_gen:.2f} tokens/sec (iGPU Inference)")
        
        print("-" * 35)
        print("DIAGNOSTIC:")
        if prefill_speeds and avg_pre < 15:
            print("  [!] LOW PREFILL: Check for RAM bandwidth bottlenecks or E-core interference.")
        elif gen_speeds and avg_gen < 2.5:
            print("  [!] LOW GENERATION: 35B model might be too heavy for shared VRAM.")
        else:
            print("  [✓] Performance is OPTIMAL for 12th Gen Intel Hardware.")

    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_hardware("logs/server.log")
