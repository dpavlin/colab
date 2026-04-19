import re
import sys
from collections import defaultdict

def audit_lifecycle(file_path):
    patterns = {
        "ts": re.compile(r"^(\d+\.\d+\.\d+\.\d+)"),
        "ingress": re.compile(r"log_server_r: request:\s+(\{.*\})"),
        "task_assigned": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)"),
        "done": re.compile(r"done request: (POST|GET) (.*) (\d{3})"),
    }

    # Tracking
    pending_ingress_ts = None
    completed_tasks = [] # list of (tid, duration_sec, type)
    total_requests = 0
    
    print(f"\nREQUEST & TASK LIFECYCLE DEEP-DIVE")
    print("=" * 80)

    def ts_to_sec(ts_str):
        # Format: MM.SS.mmm.uuu
        parts = ts_str.split('.')
        return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 1000

    try:
        current_task_map = {} # tid -> start_ts

        with open(file_path, 'r') as f:
            for line in f:
                ts_m = patterns["ts"].search(line)
                if not ts_m: continue
                timestamp = ts_m.group(1)

                # 1. Track Ingress (Start of HTTP request)
                req_m = patterns["ingress"].search(line)
                if req_m:
                    total_requests += 1
                    pending_ingress_ts = timestamp
                    continue

                # 2. Link Ingress to Task ID
                task_m = patterns["task_assigned"].search(line)
                if task_m:
                    sid, tid = task_m.groups()
                    if tid not in current_task_map:
                        current_task_map[tid] = pending_ingress_ts or timestamp

                # 3. Track Completion
                if "done request:" in line:
                    if current_task_map:
                        # Find the oldest task and assume it's the one that finished
                        tid = min(current_task_map.keys())
                        start_ts = current_task_map.pop(tid)
                        
                        duration = ts_to_sec(timestamp) - ts_to_sec(start_ts)
                        completed_tasks.append((tid, duration))

        print(f"LIFECYCLE SUMMARY:")
        print(f"  Total Requests:     {total_requests}")
        print(f"  Tasks Fully Audited: {len(completed_tasks)}")
        print("-" * 40)
        
        print(f"{'TASK ID'.ljust(10)} {'DURATION'.ljust(15)} {'STATUS'}")
        print("-" * 40)
        
        total_time = 0
        for tid, duration in completed_tasks[-10:]:
            total_time += duration
            status = "[✓] DONE" if duration > 0 else "[?] INSTANT"
            print(f"Task {tid.ljust(5)} {duration:6.2f} sec      {status}")

        print("-" * 40)
        if completed_tasks:
            avg = total_time / len(completed_tasks[-10:])
            print(f"  Average Processing Time: {avg:.2f} seconds")
        
        print("-" * 40)
        print("DIAGNOSTIC:")
        if any(d > 300 for _, d in completed_tasks):
            print("  [!] LONG TASKS: Some sessions took >5 mins. Correlate with Cache Audit.")
        else:
            print("  [✓] THROUGHPUT: All recent tasks completed in reasonable time.")

    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_lifecycle("logs/server.log")
