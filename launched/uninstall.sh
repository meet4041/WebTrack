#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT_DIR/.webtrack.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "WebTrack is not running"
  exit 0
fi

PID="$(<"$PID_FILE")"

if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "WebTrack stopped"
else
  echo "WebTrack was not running"
fi

rm -f "$PID_FILE"
