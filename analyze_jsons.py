import json
import os
import sys
from pathlib import Path
from collections import defaultdict

def analyze_value(val, path, stats):
    """Recursively analyze value types and structure with value sampling."""
    val_type = type(val).__name__
    stats[path]['types'].add(val_type)
    
    # Sample value (avoid long strings/large objects)
    sample = str(val)[:100]
    if len(str(val)) > 100:
        sample += "..."
    stats[path]['samples'].add(sample)

    if isinstance(val, dict):
        for k, v in val.items():
            new_path = f"{path}.{k}" if path else k
            analyze_value(v, new_path, stats)
    elif isinstance(val, list):
        if val:
            list_path = f"{path}[]"
            for item in val:
                analyze_value(item, list_path, stats)
        else:
            stats[f"{path}[]"]['types'].add("empty_list")

def analyze_directory(directory):
    # file_stats[group_name][path] -> {types: set, samples: set}
    file_stats = defaultdict(lambda: defaultdict(lambda: {'types': set(), 'samples': set()}))
    tmp_path = Path(directory).expanduser()
    
    if not tmp_path.exists():
        print(f"[DEBUG] Directory {tmp_path} does not exist.")
        return

    json_files = list(tmp_path.rglob("*.json"))
    print(f"[DEBUG] Found {len(json_files)} JSON files.")

    processed_count = 0
    for json_file in json_files:
        filename = json_file.name
        # Group all checkpoint-N.json files together for analysis
        group_name = filename
        if filename.startswith("checkpoint-") and filename.endswith(".json"):
            group_name = "checkpoint-*.json"
            
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            analyze_value(data, "", file_stats[group_name])
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"[DEBUG] Processed {processed_count}/{len(json_files)} files...")
        except Exception as e:
            print(f"[DEBUG] Error reading {json_file}: {e}")

    # Print summary
    print(f"\n--- Analysis Summary ({processed_count} files processed) ---")
    try:
        for group_name, stats in sorted(file_stats.items()):
            print(f"\n--- Group: '{group_name}' ---")
            for path in sorted(stats.keys()):
                types = ", ".join(sorted(stats[path]['types']))
                # Limit samples to 2 for brevity
                samples = list(stats[path]['samples'])[:2]
                print(f"  {path:50} : Types: {types}")
                for s in samples:
                    print(f"    Sample: {s}")
    except BrokenPipeError:
        # Gracefully handle piping to tools like 'head'
        sys.stderr.close()

if __name__ == "__main__":
    analyze_directory("~/.gemini/tmp")
