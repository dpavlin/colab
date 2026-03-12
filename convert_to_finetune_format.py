import json
import sys
from pathlib import Path

def convert_to_sharegpt(input_file, output_file):
    """Convert JSONL messages to ShareGPT format for Unsloth/LLaMA-Factory."""
    print(f"[DEBUG] Reading from {input_file}...")
    
    converted_count = 0
    total_turns = 0
    
    with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
        for line in f_in:
            try:
                data = json.loads(line)
                messages = data.get('messages', [])
                if not messages:
                    continue
                
                sharegpt_msgs = []
                for msg in messages:
                    role = msg['role']
                    content = msg['content']
                    
                    # Map roles to ShareGPT format
                    if role == 'user':
                        from_role = 'human'
                        value = content
                    elif role == 'assistant':
                        from_role = 'gpt'
                        value = content
                    elif role == 'system':
                        # Handle tool results as GPT observations
                        from_role = 'gpt'
                        value = f"Observation: {content}"
                    else:
                        continue
                    
                    sharegpt_msgs.append({"from": from_role, "value": value})
                    total_turns += 1
                
                if sharegpt_msgs:
                    # Final ShareGPT object
                    sharegpt_obj = {"conversations": sharegpt_msgs}
                    f_out.write(json.dumps(sharegpt_obj) + "\n")
                    converted_count += 1
                    
            except Exception as e:
                print(f"[DEBUG] Error converting line: {e}")

    print(f"[DEBUG] Conversion complete.")
    print(f"[DEBUG] Total Conversations: {converted_count}")
    print(f"[DEBUG] Total Turns (Messages): {total_turns}")
    print(f"[DEBUG] Saved to {output_file}")

if __name__ == "__main__":
    convert_to_sharegpt("comprehensive_training_data.jsonl", "sharegpt_training_data.jsonl")
