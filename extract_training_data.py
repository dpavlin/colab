import json
import os
import re
import sys
import multiprocessing
from pathlib import Path
from collections import defaultdict

# --- SECRET SCRUBBING REGEX PATTERNS ---
SECRET_PATTERNS = {
    "API_KEY": re.compile(r"(?:api[_-]key|access[_-]token|auth[_-]token|secret|key|token)[:=]\s*['\"]([a-zA-Z0-9]{16,128})['\"]", re.IGNORECASE),
    "PASSWORD": re.compile(r"(?:password|pwd|passwd|psk|pass)[:=]\s*['\"](.*?)['\"]", re.IGNORECASE),
    "IPV4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "SSH_KEY": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----", re.DOTALL),
    "GENERIC_SECRET": re.compile(r"(?:secret_key|client_secret|client_id)[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]", re.IGNORECASE),
}

def scrub_text(text):
    """Redact sensitive information from text using regex."""
    if not isinstance(text, str):
        return str(text)
    
    scrubbed = text
    for label, pattern in SECRET_PATTERNS.items():
        # Using a lambda to keep the surrounding context but replace the sensitive part
        if label in ["API_KEY", "PASSWORD", "GENERIC_SECRET"]:
            # For these, we want to replace the captured group (the actual secret)
            def redact(match):
                full_match = match.group(0)
                secret = match.group(1) if len(match.groups()) > 0 else ""
                if secret:
                    return full_match.replace(secret, f"<{label}_REDACTED>")
                return f"<{label}_REDACTED>"
            scrubbed = pattern.sub(redact, scrubbed)
        else:
            # For simpler ones (IPs, Emails), replace the whole match
            scrubbed = pattern.sub(f"<{label}_REDACTED>", scrubbed)
            
    return scrubbed

def process_file_to_pairs(json_file):
    """Worker function to extract scrubbed instruction-response pairs."""
    filename = json_file.name
    pairs = []
    
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            
        # Strategy A: logs.json (Simple pairs)
        if filename == "logs.json":
            # Sort by timestamp to preserve order
            data.sort(key=lambda x: x.get('timestamp', ''))
            for i in range(len(data) - 1):
                if data[i]['type'] == 'user' and data[i+1]['type'] == 'model':
                    pairs.append({
                        "instruction": scrub_text(data[i]['message']),
                        "output": scrub_text(data[i+1]['message'])
                    })
                    
        # Strategy B: session-*.json (Full project context)
        elif filename.startswith("session-") and filename.endswith(".json"):
            messages = data.get('messages', [])
            for i in range(len(messages) - 1):
                if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'model':
                    # User instruction
                    instr_parts = [p.get('text', '') for p in messages[i].get('parts', [])]
                    instruction = " ".join(instr_parts)
                    
                    # Model response (can be text + tool calls)
                    model_parts = []
                    for p in messages[i+1].get('parts', []):
                        if 'text' in p:
                            model_parts.append(p['text'])
                        if 'functionCall' in p:
                            model_parts.append(f"[TOOL_CALL: {p['functionCall']['name']}({json.dumps(p['functionCall']['args'])})]")
                            
                    output = "\n".join(model_parts)
                    if instruction.strip() and output.strip():
                        pairs.append({
                            "instruction": scrub_text(instruction),
                            "output": scrub_text(output)
                        })

        # Strategy C: checkpoint-*.json (History snapshots)
        elif filename.startswith("checkpoint-") and filename.endswith(".json"):
            history = data if isinstance(data, list) else data.get('history', [])
            for i in range(len(history) - 1):
                if history[i]['role'] == 'user' and history[i+1]['role'] == 'model':
                    instruction = " ".join([p.get('text', '') for p in history[i].get('parts', [])])
                    output = " ".join([p.get('text', '') for p in history[i+1].get('parts', [])])
                    if instruction.strip() and output.strip():
                        pairs.append({
                            "instruction": scrub_text(instruction),
                            "output": scrub_text(output)
                        })

        return pairs
    except Exception as e:
        print(f"[DEBUG] Error processing {json_file}: {e}")
        return []

def run_extraction(directory, output_file):
    tmp_path = Path(directory).expanduser()
    if not tmp_path.exists():
        print(f"[DEBUG] Directory {tmp_path} does not exist.")
        return

    json_files = list(tmp_path.rglob("*.json"))
    print(f"[DEBUG] Found {len(json_files)} JSON files. Extracting with {multiprocessing.cpu_count()} CPUs...")

    with multiprocessing.Pool() as pool:
        results = pool.map(process_file_to_pairs, json_files)

    # Flatten the results
    all_pairs = [pair for sublist in results for pair in sublist]
    print(f"[DEBUG] Successfully extracted {len(all_pairs)} training pairs.")

    # Save as JSONL
    output_path = Path(output_file)
    with open(output_path, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + "\n")
            
    print(f"[DEBUG] Data saved to {output_path}")

if __name__ == "__main__":
    run_extraction("~/.gemini/tmp", "training_data.jsonl")
