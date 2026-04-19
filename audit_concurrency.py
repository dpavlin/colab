import re
import sys
from collections import defaultdict

def audit_concurrency(file_path):
    # Patterns for tracking task interference
    patterns = {
        "ts": re.compile(r"^(\d+\.\d+\.\d+\.\d+)"),
        "new_request": re.compile(r"log_server_r: request:\s+(\{.*\})"),
        "task_activity": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)"),
        "prefill": re.compile(r"prompt processing progress, n_tokens = (\d+).*progress = ([\d.]+)"),
        "gen": re.compile(r"decoding batch, n_tokens = (\d+)"),
        "done": re.compile(r"done request: (POST|GET) (.*) (\d{3})"),
        "cancel": re.compile(r"cancel task, id_task = (\d+)")
    }

    active_tasks = {} # task_id -> {start_ts, slot, last_progress}
    overlaps = []
    task_count = 0
    
    print(f"\nCONCURRENCY & INTERFERENCE AUDIT")
    print("=" * 80)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                ts_m = patterns["ts"].search(line)
                if not ts_m: continue
                timestamp = ts_m.group(1)

                # 1. Detect New Request
                if "log_server_r: request:" in line:
                    task_count += 1
                    # Note: request line doesn't have task_id yet, it gets assigned in next slot update
                    continue

                # 2. Track Task Activity in Slots
                slot_m = patterns["task_activity"].search(line)
                if slot_m:
                    sid, tid = slot_m.groups()
                    
                    if tid not in active_tasks:
                        # Check for interference
                        if active_tasks:
                            others = [f"Task {t} (Slot {active_tasks[t]['slot']})" for t in active_tasks]
                            overlaps.append(f"[{timestamp}] INTERFERENCE: Task {tid} started while {', '.join(others)} active")
                        
                        active_tasks[tid] = {"start": timestamp, "slot": sid, "type": "IDLE"}

                    # Update task state
                    if patterns["prefill"].search(line):
                        active_tasks[tid]["type"] = "PREFILLING"
                    elif patterns["gen"].search(line):
                        active_tasks[tid]["type"] = "GENERATING"

                # 3. Task Completion/Removal
                if "done request:" in line:
                    # Logic to find which task finished is slightly complex in logs, 
                    # but we can clear finished slots
                    pass
                
                cancel_m = patterns["cancel"].search(line)
                if cancel_m:
                    tid = cancel_m.group(1)
                    if tid in active_tasks:
                        del active_tasks[tid]

        print(f"OVERLAP TIMELINE (Interference Events):")
        if not overlaps:
            print("  [✓] No task overlaps detected. Server operated sequentially.")
        else:
            for event in overlaps[-20:]: # Show last 20 events
                print(f"  {event}")

        print("-" * 30)
        print(f"CONCURRENCY SUMMARY:")
        print(f"  Total Requests observed:   {task_count}")
        print(f"  Total Interference events: {len(overlaps)}")
        print("-" * 30)
        print("EXPLANATION:")
        print("  When 'INTERFERENCE' is flagged, your GPU is context-switching between")
        print("  multiple slots. This causes spiky CPU/GPU usage and increases the")
        print("  Time-To-First-Token for your main prompt.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_concurrency("logs/server.log")
