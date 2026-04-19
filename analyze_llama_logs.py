import re
import sys
from collections import Counter, defaultdict

def analyze_logs(file_path):
    # Regex patterns for b8848 high-resolution accounting
    patterns = {
        "ts": re.compile(r"^(\d+\.\d+\.\d+\.\d+)"),
        "request": re.compile(r"log_server_r: request:\s+(\{.*\})"),
        "slot": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)\s+\|\s+(.*)"),
        "checkpoint": re.compile(r"created context checkpoint (\d+).*n_tokens = (\d+)"),
        "batch": re.compile(r"decoding batch, n_tokens = (\d+)"),
        "progress": re.compile(r"prompt processing progress, n_tokens = (\d+)"),
        "gpu": re.compile(r"offloaded (\d+)/(\d+) layers to GPU"),
        "error": re.compile(r"(error|failed|exception|cancel|abort)", re.IGNORECASE),
        "grammar": re.compile(r"(Literal|Atomic|Tag|Rule|Sequence|Choice|Repetition|Space)"),
        "system": re.compile(r"(I main:|I build_info:|I system_info:|init: using|Running without SSL|done request)")
    }

    stats = Counter()
    timeline = []
    
    print(f"\nFINAL UNIFIED AUDIT: {file_path}")
    print("=" * 100)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                stats["total_lines"] += 1
                matched = False
                
                ts_m = patterns["ts"].search(line)
                timestamp = ts_m.group(1) if ts_m else "N/A"

                if patterns["gpu"].search(line):
                    m = patterns["gpu"].search(line)
                    stats["gpu_config"] = f"{m.group(1)}/{m.group(2)}"
                    matched = True

                if "log_server_r: request:" in line:
                    stats["requests"] += 1
                    timeline.append(f"[{timestamp}] [INGRESS] New Request")
                    matched = True

                slot_m = patterns["slot"].search(line)
                if slot_m:
                    sid, tid, msg = slot_m.groups()
                    if "n_tokens =" in msg:
                        tokens = int(re.search(r"n_tokens = (\d+)", msg).group(1))
                        if tokens > 100:
                            stats["cache_hits"] += 1
                            timeline.append(f"[{timestamp}] [CACHE] Slot {sid} REUSED {tokens} tokens")
                        else:
                            timeline.append(f"[{timestamp}] [PREFILL] Slot {sid} started at 0")
                    if "decoding batch" in msg: stats["gen_steps"] += 1
                    matched = True

                cp_m = patterns["checkpoint"].search(line)
                if cp_m:
                    stats["checkpoints"] += 1
                    timeline.append(f"[{timestamp}] [SNAPSHOT] State Checkpoint at {cp_m.group(2)} tokens")
                    matched = True

                if patterns["error"].search(line) and not patterns["grammar"].search(line):
                    stats["anomalies"] += 1
                    timeline.append(f"[{timestamp}] [ALERT] {line[:80]}")
                    matched = True

                if patterns["grammar"].search(line):
                    stats["grammar_lines"] += 1
                    matched = True

                if patterns["system"].search(line) or patterns["progress"].search(line):
                    matched = True

                if not matched: stats["unaccounted"] += 1

        print(f"1. HARDWARE: {stats.get('gpu_config', 'N/A')} Layers on GPU")
        print(f"2. REQUESTS: {stats['requests']} total sessions handled")
        print(f"3. CACHE:    {stats['cache_hits']} fast reuses, {stats['checkpoints']} state checkpoints")
        print(f"4. COMPUTE:  {stats['gen_steps']} token generation batches")
        print("-" * 50)
        print("LATEST SYSTEM EVENTS:")
        for event in timeline[-15:]:
            print(f"   {event}")
        print("-" * 50)
        
        coverage = ((stats['total_lines'] - stats['unaccounted']) / stats['total_lines']) * 100
        print(f"AUDIT COVERAGE: {coverage:.2f}% ({stats['grammar_lines']} template lines accounted)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_logs("logs/server.log")
