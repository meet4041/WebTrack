from __future__ import annotations

from pathlib import Path

APP_NAME = "WebTrack"
POLL_INTERVAL_SECONDS = 1.0

HOME = Path.home()
DESKTOP_DIR = HOME / "Desktop"
APP_DIR = DESKTOP_DIR / "Browser history"
HISTORY_DIR = APP_DIR / "History"
STATE_DIR = APP_DIR / ".state"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = APP_DIR / "webtrack.log"

SUPPORTED_BROWSERS = {"Google Chrome", "Safari"}
