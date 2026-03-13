import json
import subprocess
import requests
import sys
import os

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-7b-q4km"

def execute_tool(name, args):
    """Executes the requested tool locally and returns the result."""
    name_lower = name.lower()
    print(f"\n>> EXECUTING: {name}({args})")
    
    if name_lower in ["list_directory", "list_directory_content", "list_files"]:
        path = args.get("dir_path") or args.get("path") or "."
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            return f"Error: {e}"
            
    elif name_lower == "run_shell_command":
        cmd = args.get("command")
        if not cmd: return "Error: No command provided"
        
        # SAFETY: Ask user before running shell commands
        confirm = input(f"Confirm execution of: {cmd} (y/n)? ")
        if confirm.lower() != 'y':
            return "Error: User denied command execution."
            
        try:
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return f"Command failed with exit code {e.returncode}: {e.output}"
            
    elif name_lower == "read_file":
        path = args.get("file_path") or args.get("absolute_path")
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error: {e}"
            
    return f"Error: Unknown tool '{name}'"

def run_conversation(user_input, max_iterations=10):
    messages = [{"role": "user", "content": user_input}]
    previous_calls = set()
    
    for i in range(max_iterations):
        # 1. Ask the model
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False
            })
            response.raise_for_status()
        except Exception as e:
            print(f">> API ERROR: {e}")
            break
            
        resp_json = response.json()
        assistant_msg = resp_json['message']['content']
        print(f"\nAssistant: {assistant_msg}")
        
        messages.append({"role": "assistant", "content": assistant_msg})
        
        # 2. Check for Tool Call
        if "[TOOL_CALL]" in assistant_msg:
            try:
                # Extract the part after [TOOL_CALL]
                call_part = assistant_msg.split("[TOOL_CALL]")[1].strip()
                
                # Detect loop: if we see the exact same call twice, stop
                if call_part in previous_calls:
                    print(">> LOOP DETECTED: Repeating the same tool call. Breaking.")
                    break
                previous_calls.add(call_part)

                # Remove "CALL:" if present
                if call_part.startswith("CALL:"):
                    call_part = call_part.replace("CALL:", "", 1).strip()
                
                # Split name and JSON args
                if "(" in call_part and "{" in call_part:
                    name = call_part.split("(")[0].strip()
                    args_str = call_part[call_part.find("(")+1 : call_part.rfind(")")].strip()
                    
                    # Try to fix unquoted keys if JSON loading fails
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        import re
                        # Basic regex to quote unquoted keys
                        quoted_args = re.sub(r'(\w+):', r'"\1":', args_str)
                        try:
                            args = json.loads(quoted_args)
                        except:
                            # Final fallback to shell
                            name = "run_shell_command"
                            args = {"command": call_part}
                else:
                    # Fallback: treat as direct shell command
                    name = "run_shell_command"
                    args = {"command": call_part}
                
                # 3. Execute and feed back
                result = execute_tool(name, args)
                print(f">> RESULT: {result[:200]}...")
                
                messages.append({"role": "system", "content": f"[TOOL_RESULT] {result}"})
                # Loop continues to let the model see the result
                continue
            except Exception as e:
                print(f">> FAILED TO PARSE TOOL CALL: {e}")
                break
        else:
            # No more tool calls, we are done
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_conversation(" ".join(sys.argv[1:]))
    else:
        while True:
            inp = input("\nUser: ")
            if inp.lower() in ["exit", "quit"]: break
            run_conversation(inp)
