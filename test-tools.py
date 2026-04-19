import os
from openai import OpenAI
import json

# Connect to your local llama-server
client = OpenAI(
    base_url="http://localhost:8085/v1",
    api_key="sk-no-key-required"
)

# Define a sample tool (the model will decide when to use it)
def get_current_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
]

print("Sending request to Qwen 3.6...")

response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "What time is it right now?"}
    ],
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

if message.tool_calls:
    print("\n[Tool Call Detected]")
    for tool_call in message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
        
        # In a real agent, you would execute the function here and send the result back.
        if tool_call.function.name == "get_current_time":
            result = get_current_time()
            print(f"Executed result: {result}")
else:
    print("\n[Normal Response]")
    print(message.content)
