#!/usr/bin/env bash

# local-llm dictation script using whisper.cpp with Vulkan GPU acceleration.
# Dependencies: arecord, whisper-cli, xdotool, xclip, notify-send

set -euo pipefail

# Configurations
WHISPER_DIR="/nuc/whisper.cpp"
WHISPER_CLI="${WHISPER_DIR}/build/bin/whisper-cli"
MODEL_PATH="${WHISPER_DIR}/models/ggml-large-v3-turbo-q5_0.bin"
LANG_CODE="auto"  # Spoken language: 'hr' for Croatian, 'en' for English, or 'auto' for auto-detect
ALLOWED_LANGS="en,hr" # Filter auto-detected languages when LANG_CODE="auto" (helps avoid false translations/mismatches)
AUDIO_FILE="/tmp/dictation.wav"
PID_FILE="/tmp/dictation.pid"

# Debug output helper
debug_log() {
    echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# Optional desktop notification wrapper
notify() {
    local title="$1"
    local msg="$2"
    local urgency="${3:-normal}"
    if command -v notify-send &>/dev/null; then
        notify-send -u "$urgency" "$title" "$msg"
    fi
}

# Play feedback sound if available
play_sound() {
    local mode="${1:-start}"
    local sound_file="/usr/share/sounds/freedesktop/stereo/bell.oga"
    
    if [[ "$mode" == "stop" ]]; then
        sound_file="/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"
    fi

    if [[ -f "$sound_file" ]] && command -v paplay &>/dev/null; then
        paplay "$sound_file" 2>/dev/null || true
    fi
}

# Verify dependencies
verify_dependencies() {
    local missing=()
    for cmd in ffmpeg xdotool xclip; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ! -f "$WHISPER_CLI" ]]; then
        missing+=("whisper-cli (at $WHISPER_CLI)")
    fi
    
    if [[ ! -f "$MODEL_PATH" ]]; then
        missing+=("whisper model (at $MODEL_PATH)")
    fi

    if [[ ${#missing[@]} -ne 0 ]]; then
        debug_log "Missing dependencies: ${missing[*]}"
        notify "Dictation Error" "Missing dependencies: ${missing[*]}" critical
        exit 1
    fi
}

start_recording() {
    debug_log "Starting recording..."
    
    # Dynamically detect active bluetooth input source
    local device="default"
    if command -v pactl &>/dev/null; then
        local bt_source
        bt_source=$(pactl list sources short | grep -o -E 'bluez_input\.[A-Za-z0-9_.:-]+' | head -n 1 || true)
        if [[ -n "$bt_source" ]]; then
            device="$bt_source"
            debug_log "Detected Bluetooth microphone: $device"
            notify "Dictation" "Recording from Bluetooth headphones..."
        else
            debug_log "No Bluetooth microphone detected. Using default source: $device"
            notify "Dictation" "Recording started... Speak now."
        fi
    else
        notify "Dictation" "Recording started... Speak now."
    fi

    # 1. Play a double-chime BEFORE recording starts:
    # First play wakes the Bluetooth headphones from suspend (often cut off).
    # Second play (after 0.6s) is fully heard as the device is now active.
    play_sound start
    sleep 0.6
    play_sound start

    # 2. Clean up previous audio
    rm -f "$AUDIO_FILE"

    # 3. Record at 16kHz mono 16-bit PCM (Whisper native format) using ffmpeg
    ffmpeg -y -loglevel quiet -f pulse -i "$device" -ar 16000 -ac 1 -c:a pcm_s16le "$AUDIO_FILE" &
    local record_pid=$!
    
    # Save PID
    echo "$record_pid" > "$PID_FILE"
    debug_log "Recording process started with PID: $record_pid"

    # 4. Wait 1.2s for the Bluetooth duplex recording stream to fully establish and stabilize
    # (The user knows to wait a brief moment after hearing the chime before speaking)
    sleep 1.2
}

stop_recording_and_transcribe() {
    if [[ ! -f "$PID_FILE" ]]; then
        debug_log "No recording process found."
        exit 1
    fi

    local record_pid
    record_pid=$(cat "$PID_FILE")
    rm -f "$PID_FILE"

    debug_log "Stopping recording process (PID: $record_pid)..."
    if kill -0 "$record_pid" 2>/dev/null; then
        kill -INT "$record_pid"
        wait "$record_pid" 2>/dev/null || true
    fi
    
    play_sound stop
    notify "Dictation" "Transcribing audio..."

    if [[ ! -f "$AUDIO_FILE" || ! -s "$AUDIO_FILE" ]]; then
        debug_log "Audio file is empty or missing."
        notify "Dictation" "Error: Audio file is empty." critical
        exit 1
    fi

    debug_log "Running transcription using Vulkan GPU..."
    # Capture transcription from stdout, suppress stderr logs
    local text
    text=$(WHISPER_ALLOWED_LANGS="$ALLOWED_LANGS" "$WHISPER_CLI" -m "$MODEL_PATH" -f "$AUDIO_FILE" -l "$LANG_CODE" -nt 2>/dev/null || true)
    
    # Clean up the output text
    text=$(echo "$text" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/\[[^]]*\]//g')

    if [[ -z "$text" ]]; then
        debug_log "No speech recognized."
        notify "Dictation" "No speech recognized."
        exit 0
    fi

    debug_log "Recognized text: '$text'"
    notify "Dictation" "Dictated: $text"

    # Copy to clipboard & primary selection as fallback
    echo -n "$text" | xclip -selection clipboard
    echo -n "$text" | xclip -selection primary

    # Brief delay to allow hotkey release before typing
    sleep 0.2

    # Paste into currently focused client
    debug_log "Typing text into focused window..."
    xdotool type --clearmodifiers --delay 2 "$text "
}

# Main routing logic
verify_dependencies

# Parse arguments
TOGGLE_MODE=false
if [[ $# -gt 0 && "$1" == "--toggle" ]]; then
    TOGGLE_MODE=true
fi

if [ "$TOGGLE_MODE" = true ]; then
    if [[ -f "$PID_FILE" ]]; then
        # Second press: stop and transcribe
        stop_recording_and_transcribe
    else
        # First press: start recording
        start_recording
    fi
else
    # Terminal interactive mode
    start_recording
    echo "============================================="
    echo " Recording... Speak now."
    echo " Press [Enter] to stop and paste."
    echo "============================================="
    read -r _
    stop_recording_and_transcribe
fi
