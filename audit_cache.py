import re
import sys
from collections import defaultdict

def audit_cache(file_path):
    patterns = {
        "new_task": re.compile(r"task (\d+) \| new prompt.*task\.n_tokens = (\d+)"),
        "checkpoint_created": re.compile(r"created context checkpoint (\d+).*n_tokens = (\d+)"),
        "checkpoint_restored": re.compile(r"restored context checkpoint.*n_tokens = (\d+)"),
        "checkpoint_erased": re.compile(r"erased invalidated context checkpoint.*n_tokens = (\d+)"),
        "token_reuse": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)\s+\|\s+n_tokens = (\d+)"),
    }

    stats = {
        "restored_tokens": 0,
        "created": 0,
        "restored_count": 0,
        "invalidated": 0,
        "total_reuse_events": 0
    }
    
    print(f"\nQWEN 3.6 RECURRENT CACHE AUDIT")
    print("=" * 60)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 1. Track Snapshot Creation
                if patterns["checkpoint_created"].search(line):
                    stats["created"] += 1

                # 2. Track Restorations (The "Instant Prefill" events)
                res_m = patterns["checkpoint_restored"].search(line)
                if res_m:
                    stats["restored_count"] += 1
                    stats["restored_tokens"] += int(res_m.group(1))

                # 3. Track Branching Cleanup (Invalidations)
                if patterns["checkpoint_erased"].search(line):
                    stats["invalidated"] += 1

                # 4. General Reuse
                reuse_m = patterns["token_reuse"].search(line)
                if reuse_m:
                    if int(reuse_m.group(3)) > 100:
                        stats["total_reuse_events"] += 1

        print(f"CACHE EFFICIENCY:")
        print(f"  Total Prefill Saves:   {stats['restored_count']} restorations")
        print(f"  Total Tokens Reused:   {stats['restored_tokens']:,} tokens")
        print(f"  Estimated Time Saved:  {int(stats['restored_tokens'] / 22 / 60)} minutes")
        print("-" * 30)

        print(f"RECURRENT STATE MANAGEMENT:")
        print(f"  Snapshots Created:     {stats['created']}")
        print(f"  Snapshots Invalidated: {stats['invalidated']} (Due to conversation branching)")
        print("-" * 30)
        
        print("VERIFICATION:")
        if stats['restored_count'] > 0:
            print(f"  [✓] Recurrent cache is ACTIVE and performing instant restorations.")
        else:
            print(f"  [!] No restorations found. Verify system prompt stability.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_cache("logs/server.log")
