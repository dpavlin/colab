#!/bin/bash

# Configuration
PORT=8085
URL="http://localhost:$PORT"

echo "LLM Server Status Monitor (Ctrl+C to exit)"
echo "------------------------------------------"

while true; do
    # Clear line and move cursor to top
    clear
    echo "Time: $(date +%H:%M:%S)"
    echo "------------------------------------------"

    # 1. Check Slot Status (What is it doing right now?)
    SLOT_INFO=$(curl -s "$URL/slots")
    if [ $? -ne 0 ]; then
        echo "Error: Cannot connect to server on port $PORT"
    else
        echo "SLOT STATUS:"
        echo "$SLOT_INFO" | jq -r '.[] | "Slot \(.id): \(.state) | Prompt: \(.n_prompt_tokens) | Decoded: \(.n_decoded_tokens) | Processing: \(.is_processing)"'
    fi

    echo "------------------------------------------"

    # 2. Check Metrics (Accumulated work)
    METRICS=$(curl -s "$URL/metrics")
    if [ ! -z "$METRICS" ]; then
        P_TOKENS=$(echo "$METRICS" | grep "llamacpp:prompt_tokens_total" | awk '{print $2}')
        G_TOKENS=$(echo "$METRICS" | grep "llamacpp:tokens_predicted_total" | awk '{print $2}')
        echo "CUMULATIVE METRICS:"
        echo "Prompt Tokens Processed: $P_TOKENS"
        echo "Tokens Generated:       $G_TOKENS"
    fi

    echo "------------------------------------------"
    echo "LAST 5 LOG ENTRIES:"
    tail -n 5 logs/server.log | cut -c 1-100
    
    sleep 1
done
