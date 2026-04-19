#!/bin/bash

# Port should match your llama-server port
PORT=8085

echo "Monitoring Qwen 3.6 tokens on port $PORT..."
echo "This script will wait for requests and print generated tokens to this console."
echo "Press Ctrl+C to stop."

# We use a long-lived connection to monitor metrics or we can just tail the log
# But a better way is to provide a wrapper that you can use to send prompts:

if [ "$#" -eq 0 ]; then
    echo ""
    echo "Usage: ./monitor-tokens.sh \"Your prompt here\""
    echo "Example: ./monitor-tokens.sh \"Write a python script to list files\""
    exit 0
fi

PROMPT="$*"

curl -s -N http://localhost:$PORT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],
    \"stream\": true
  }" | while read -r line; do
    # Extract content from the SSE data stream
    content=$(echo "$line" | grep -o '"content":"[^"]*"' | sed 's/"content":"//;s/"//g')
    if [ ! -z "$content" ]; then
        # Handle newlines and special chars
        printf "%b" "$content"
    fi
done
echo ""
