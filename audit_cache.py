import re
import sys
from collections import defaultdict

def audit_cache(file_path):
    patterns = {
        "checkpoint_created": re.compile(r"created context checkpoint (\d+).*size = ([\d.]+) MiB"),
        "checkpoint_restored": re.compile(r"restored context checkpoint.*n_tokens = (\d+)"),
        "checkpoint_erased": re.compile(r"erased invalidated context checkpoint.*size = ([\d.]+) MiB"),
        "token_reuse": re.compile(r"slot update_slots: id\s+(\d+)\s+\|\s+task\s+(\d+)\s+\|\s+n_tokens = (\d+)"),
    }

    stats = {
        "restored_tokens": 0,
        "created_count": 0,
        "restored_count": 0,
        "erased_count": 0,
        "current_ram_mib": 0.0,
        "peak_ram_mib": 0.0
    }
    
    print(f"\nQWEN 3.6 RECURRENT CACHE AUDIT (RAM-FOCUS)")
    print("=" * 70)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 1. Track Snapshot Creation & RAM Usage
                cp_c = patterns["checkpoint_created"].search(line)
                if cp_c:
                    stats["created_count"] += 1
                    size = float(cp_c.group(2))
                    stats["current_ram_mib"] += size
                    if stats["current_ram_mib"] > stats["peak_ram_mib"]:
                        stats["peak_ram_mib"] = stats["current_ram_mib"]

                # 2. Track Restorations
                res_m = patterns["checkpoint_restored"].search(line)
                if res_m:
                    stats["restored_count"] += 1
                    stats["restored_tokens"] += int(res_m.group(1))

                # 3. Track Erasures (Freeing RAM)
                cp_e = patterns["checkpoint_erased"].search(line)
                if cp_e:
                    stats["erased_count"] += 1
                    size = float(cp_e.group(1))
                    stats["current_ram_mib"] -= size

        print(f"CACHE EFFICIENCY:")
        print(f"  Total Tokens Reused:   {stats['restored_tokens']:,} tokens")
        print(f"  Time Saved (Est):      {int(stats['restored_tokens'] / 22 / 60)} minutes")
        print("-" * 35)

        print(f"MEMORY ACCOUNTING (Recurrent States):")
        print(f"  Active Snapshots:      {stats['created_count'] - stats['erased_count']}")
        print(f"  Snapshot Erasures:     {stats['erased_count']}")
        print(f"  Current Cache RAM:     {max(0, stats['current_ram_mib']):.2f} MiB")
        print(f"  Peak Cache RAM:        {stats['peak_ram_mib']:.2f} MiB")
        print("-" * 35)
        
        print("DIAGNOSTIC:")
        if stats['peak_ram_mib'] > 2000:
            print("  [!] HIGH MEMORY: Cache is using >2GB. Consider reducing --ctx-checkpoints.")
        elif stats['restored_count'] > 0:
            print(f"  [✓] CACHE ACTIVE: Successfully performed {stats['restored_count']} instant restorations.")
        else:
            print("  [?] IDLE: No restorations detected in this log segment.")

    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_cache("logs/server.log")
