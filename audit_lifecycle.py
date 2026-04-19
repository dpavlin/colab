import re
import sys
from collections import defaultdict

def audit_lifecycle(file_path):
    patterns = {
        "ingress": re.compile(r"log_server_r: request: (\{.*\})"),
        "done": re.compile(r"done request: (POST|GET) (.*) (\d{3})"),
        "cancel": re.compile(r"cancel task, id_task = (\d+)"),
        "slot_assign": re.compile(r"selected slot by LRU, t_last = (\d+)"),
        "task_info": re.compile(r"task (\d+) \| (.*)"),
    }

    requests = []
    completed = 0
    cancelled = 0
    
    print(f"\nREQUEST & TASK LIFECYCLE DEEP-DIVE")
    print("=" * 60)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 1. Track Request Content (Truncated)
                req_m = patterns["ingress"].search(line)
                if req_m:
                    requests.append(req_m.group(1)[:100])

                # 2. Outcomes
                if patterns["done"].search(line):
                    completed += 1
                if patterns["cancel"].search(line):
                    cancelled += 1

        print(f"LIFECYCLE SUMMARY:")
        print(f"  Sessions Started:   {len(requests)}")
        print(f"  Sessions Finished:  {completed}")
        print(f"  Sessions Aborted:   {cancelled}")
        print("-" * 30)
        
        print("LAST 5 REQUEST SNIPPETS:")
        for r in requests[-5:]:
            print(f"  -> {r}...")

        print("-" * 30)
        if len(requests) > completed + cancelled:
            print(f"  [!] Note: {len(requests) - (completed + cancelled)} tasks are still pending or failed silently.")
        else:
            print("  [✓] All incoming requests are accounted for.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_lifecycle("logs/server.log")
