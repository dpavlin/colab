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
}

def scrub_text(text):
    if not isinstance(text, str): return str(text)
    scrubbed = text
    for label, pattern in SECRET_PATTERNS.items():
        if label in ["API_KEY", "PASSWORD"]:
            def redact(match):
                full = match.group(0)
                secret = match.group(1) if len(match.groups()) > 0 else ""
                return full.replace(secret, f"<{label}_REDACTED>") if secret else f"<{label}_REDACTED>"
            scrubbed = pattern.sub(redact, scrubbed)
        else:
            scrubbed = pattern.sub(f"<{label}_REDACTED>", scrubbed)
    return scrubbed

def format_message(msg):
    """Format a single message (user, gemini, or tool/system) into a role-based object."""
    role = msg.get('type') or msg.get('role')
    if role == 'gemini': role = 'assistant'
    
    content_parts = []
    
    # Handle text content
    raw_content = msg.get('content', '')
    if isinstance(raw_content, list):
        text = " ".join([p.get('text', '') for p in raw_content if 'text' in p])
    else:
        text = raw_content
    
    if text: content_parts.append(scrub_text(text))
    
    # Handle thoughts
    thoughts = msg.get('thoughts', [])
    if thoughts:
        thought_text = "\n".join([f"Thought: {t.get('subject')}: {t.get('description')}" for t in thoughts])
        content_parts.insert(0, f"<thought>\n{scrub_text(thought_text)}\n</thought>")

    # Handle tool calls and results
    tool_calls = msg.get('toolCalls', [])
    turns = []
    
    main_content = "\n".join(content_parts)
    if main_content:
        turns.append({"role": role, "content": main_content})

    for tc in tool_calls:
        # The Action
        call_info = f"CALL: {tc['name']}({json.dumps(tc['args'])})"
        turns.append({"role": "assistant", "content": f"[TOOL_CALL] {scrub_text(call_info)}"})
        
        # The Observation (Result)
        for res in tc.get('result', []):
            if 'functionResponse' in res:
                output = res['functionResponse']['response'].get('output', '')
                error = res['functionResponse']['response'].get('error', '')
                final_res = output if output else error
                turns.append({"role": "system", "content": f"[TOOL_RESULT] {scrub_text(final_res)}"})

    return turns

def process_any_file(json_file):
    """Worker function to extract scrubbed conversations from any known Gemini JSON format."""
    filename = json_file.name
    conversations = []
    
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            
        # Strategy A: logs.json (Simple User/Model pairs)
        if filename == "logs.json":
            data.sort(key=lambda x: x.get('timestamp', ''))
            messages = []
            for msg in data:
                role = 'user' if msg['type'] == 'user' else 'assistant'
                messages.append({"role": role, "content": scrub_text(msg['message'])})
            if messages: conversations.append({"messages": messages})

        # Strategy B: session-*.json (Full Agent Traces - The Best Data)
        elif filename.startswith("session-") and filename.endswith(".json"):
            messages = data.get('messages', [])
            session_turns = []
            for msg in messages:
                session_turns.extend(format_message(msg))
            if session_turns: conversations.append({"messages": session_turns})

        # Strategy C: checkpoint-*.json (Conversation Snapshots)
        elif filename.startswith("checkpoint-") and filename.endswith(".json"):
            history = data if isinstance(data, list) else data.get('history', [])
            messages = []
            for msg in history:
                role = msg.get('role', 'user')
                if role == 'gemini': role = 'assistant'
                # Extract text from parts
                text = " ".join([p.get('text', '') for p in msg.get('parts', []) if 'text' in p])
                if text: messages.append({"role": role, "content": scrub_text(text)})
            if messages: conversations.append({"messages": messages})

        return conversations
    except Exception as e:
        # Silently skip 'role' errors for files that don't match the schema
        if "role" not in str(e):
            print(f"[DEBUG] Error processing {json_file}: {e}")
        return []

def run_comprehensive_extraction(directory, output_file):
    tmp_path = Path(directory).expanduser()
    json_files = list(tmp_path.rglob("*.json"))
    print(f"[DEBUG] Found {len(json_files)} total JSON files. Extracting from all sources...")

    with multiprocessing.Pool() as pool:
        results = pool.map(process_any_file, json_files)

    all_conversations = [conv for sublist in results for conv in sublist]
    print(f"[DEBUG] Extracted {len(all_conversations)} conversations from all sources.")

    with open(output_file, "w") as f:
        for conv in all_conversations:
            f.write(json.dumps(conv) + "\n")
    print(f"[DEBUG] Saved to {output_file}")

if __name__ == "__main__":
    run_comprehensive_extraction("~/.gemini/tmp", "comprehensive_training_data.jsonl")
