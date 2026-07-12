#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT_DIR/.webtrack.pid"
OUT_FILE="$ROOT_DIR/webtrack.out"
DATA_DIR="$HOME/Desktop/Browser history"
PYTHON_BIN="${PYTHON_BIN:-/Library/Frameworks/Python.framework/Versions/3.12/bin/python3}"

if [[ -f "$PID_FILE" ]]; then
  PID="$(<"$PID_FILE")"
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    echo "WebTrack already running with PID $PID"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

mkdir -p "$DATA_DIR"
nohup "$PYTHON_BIN" "$ROOT_DIR/main.py" >>"$OUT_FILE" 2>&1 &
PID=$!
echo "$PID" >"$PID_FILE"
echo "WebTrack started in background with PID $PID"
