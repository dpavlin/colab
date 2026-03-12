import json
import subprocess
import requests
import sys
import os

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "my-agent"

def execute_tool(name, args):
    """Executes the requested tool locally and returns the result."""
    print(f"\n>> EXECUTING: {name}({args})")
    
    if name == "list_directory":
        path = args.get("dir_path", ".")
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            return f"Error: {e}"
            
    elif name == "run_shell_command":
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
            
    elif name == "read_file":
        path = args.get("file_path") or args.get("absolute_path")
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error: {e}"
            
    return f"Error: Unknown tool '{name}'"

def run_conversation(user_input):
    messages = [{"role": "user", "content": user_input}]
    
    while True:
        # 1. Ask the model
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False
        })
        
        resp_json = response.json()
        assistant_msg = resp_json['message']['content']
        print(f"\nAssistant: {assistant_msg}")
        
        messages.append({"role": "assistant", "content": assistant_msg})
        
        # 2. Check for Tool Call
        if "[TOOL_CALL]" in assistant_msg:
            # Simple parser for: [TOOL_CALL] CALL: name({"args": "..."})
            try:
                # Extract the part after CALL:
                call_part = assistant_msg.split("CALL:")[1].strip()
                name = call_part.split("(")[0]
                args_json = call_part.split("(")[1].rstrip(")")
                args = json.loads(args_json)
                
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
