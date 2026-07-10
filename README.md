# WebTrack

Local macOS browser activity tracker for Chrome and Safari.

## What it does

- Polls the active browser tab in the foreground.
- Records title, URL, start/end time, and duration.
- Writes daily text logs under `Desktop/Browser history/History`.
- Keeps all data local.

## Run

```bash
python3 main.py
```

## Notes

- Requires macOS with AppleScript access.
- The app is designed to run continuously in the background.
- State is stored locally in `Desktop/Browser history/.state/state.json`.
# WebTrack
