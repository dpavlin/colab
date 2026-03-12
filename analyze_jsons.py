import json
import os
import sys
import multiprocessing
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

def process_file(json_file):
    """Worker function to process a single JSON file."""
    filename = json_file.name
    # Group names
    group_name = filename
    if filename.startswith("checkpoint-") and filename.endswith(".json"):
        group_name = "checkpoint-*.json"
    elif filename.startswith("session-") and filename.endswith(".json"):
        group_name = "session-*.json"

    file_stats = defaultdict(lambda: {'types': set(), 'samples': set()})
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        analyze_value(data, "", file_stats)
        return group_name, file_stats
    except Exception as e:
        return None, str(e)

def analyze_directory(directory):
    tmp_path = Path(directory).expanduser()
    if not tmp_path.exists():
        print(f"[DEBUG] Directory {tmp_path} does not exist.")
        return

    json_files = list(tmp_path.rglob("*.json"))
    print(f"[DEBUG] Found {len(json_files)} JSON files. Analyzing with {multiprocessing.cpu_count()} CPUs...")

    # Using Multiprocessing Pool
    with multiprocessing.Pool() as pool:
        results = pool.map(process_file, json_files)

    # Aggregate results
    aggregated_stats = defaultdict(lambda: defaultdict(lambda: {'types': set(), 'samples': set()}))
    processed_count = 0
    errors = []

    for group_name, result in results:
        if group_name:
            processed_count += 1
            for path, stats in result.items():
                aggregated_stats[group_name][path]['types'].update(stats['types'])
                aggregated_stats[group_name][path]['samples'].update(stats['samples'])
        else:
            errors.append(result)

    if errors:
        print(f"[DEBUG] Encountered {len(errors)} errors during processing.")

    # Print summary
    print(f"\n--- Parallel Analysis Summary ({processed_count} files processed) ---")
    try:
        for group_name, stats in sorted(aggregated_stats.items()):
            print(f"\n--- Group: '{group_name}' ---")
            for path in sorted(stats.keys()):
                types = ", ".join(sorted(stats[path]['types']))
                # Limit samples to 2 for brevity
                samples = list(stats[path]['samples'])[:2]
                print(f"  {path:50} : Types: {types}")
                for s in samples:
                    print(f"    Sample: {s}")
    except BrokenPipeError:
        sys.stderr.close()

if __name__ == "__main__":
    analyze_directory("~/.gemini/tmp")
