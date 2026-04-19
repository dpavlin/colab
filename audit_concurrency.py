import re
import sys
from collections import defaultdict

def audit_concurrency(file_path):
    patterns = {
        "ts": re.compile(r"^(\d+\.\d+\.\d+\.\d+)"),
        "task_activity": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)"),
        "done": re.compile(r"done request: (POST|GET) (.*) (\d{3})"),
        "cancel": re.compile(r"cancel task, id_task = (\d+)")
    }

    # Tracking slot occupancy over logical time steps
    timeline = []
    current_slots = { "0": ".", "1": "." } # . for idle, # for busy
    
    print(f"\nCONCURRENCY HEATMAP & INTERFERENCE AUDIT")
    print("=" * 80)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                ts_m = patterns["ts"].search(line)
                if not ts_m: continue
                
                # Check for activity in specific slots
                slot_m = patterns["task_activity"].search(line)
                if slot_m:
                    sid, tid = slot_m.groups()
                    current_slots[sid] = "#"
                    
                    # Capture a "snapshot" of concurrency
                    if len(timeline) == 0 or timeline[-1][1] != f"[{current_slots['0']}{current_slots['1']}]":
                        timeline.append((ts_m.group(1), f"[{current_slots['0']}{current_slots['1']}]", tid))

                # Simple heuristic for clearing slots (llama-server logs are sparse on 'done' per slot)
                if "all slots are idle" in line:
                    current_slots = { "0": ".", "1": "." }

        print("TIME        SLOT MAP [01]   ACTIVE TASK")
        print("-" * 40)
        
        last_map = ""
        overlap_count = 0
        
        for ts, smap, tid in timeline[-30:]: # Last 30 state changes
            if smap == "[##]":
                overlap_count += 1
                indicator = "<-- INTERFERENCE"
            else:
                indicator = ""
            
            print(f"{ts.ljust(12)} {smap}          Task {tid} {indicator}")

        print("-" * 40)
        print(f"AUDIT SUMMARY:")
        print(f"  Parallel Overhead Events: {overlap_count}")
        print("-" * 40)
        print("LEGEND:")
        print("  [#.] -> Only Slot 0 active (Main Chat)")
        print("  [.#] -> Only Slot 1 active (Background Task)")
        print("  [##] -> BOTH ACTIVE (Context Switching Spike!)")

    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_concurrency("logs/server.log")
