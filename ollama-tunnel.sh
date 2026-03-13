#!/bin/bash

# Configuration
REMOTE_HOST="ollama.dhcp.ffzg.hr"
LOCAL_PORT=11434
REMOTE_PORT=11434
PID_FILE="/tmp/ollama-tunnel.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Ollama tunnel is already running (PID: $PID)"
            return
        else
            rm "$PID_FILE"
        fi
    fi

    echo "Starting Ollama tunnel to ${REMOTE_HOST}..."
    ssh -f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${REMOTE_HOST}
    
    # Wait a moment and check if it's running
    sleep 2
    PID=$(ps aux | grep "[s]sh -f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT}" | awk '{print $2}')
    
    if [ -n "$PID" ]; then
        echo "$PID" > "$PID_FILE"
        echo "Tunnel started (PID: $PID)"
    else
        echo "Failed to start tunnel."
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "Stopping Ollama tunnel (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "Tunnel stopped."
    else
        echo "Ollama tunnel is not running (no PID file)."
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Ollama tunnel is running (PID: $PID)"
            ssh -o BatchMode=yes -p $LOCAL_PORT localhost "ollama --version" 2>/dev/null && echo "Ollama API is responding on localhost:${LOCAL_PORT}"
        else
            echo "Ollama tunnel PID file exists but process is not running."
        fi
    else
        echo "Ollama tunnel is not running."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
esac
