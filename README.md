# WebTrack

Local macOS browser activity tracker for Chrome and Safari.

## What it does

- Polls the active browser tab in the foreground.
- Records title, URL, start/end time, and duration.
- Writes daily text logs under `Desktop/Browser history/History`.
- Keeps all data local.

## Run

1. Clone the repository.
```bash
git clone https://github.com/meet4041/WebTrack.git
cd WebTrack
```

2. Start WebTrack.
```bash
./launched/install.sh
```

3. Check the saved data.
- Logs are stored in `~/Desktop/Browser history/History`

4. Stop WebTrack when needed.
```bash
./launched/uninstall.sh
```

## Notes

- Requires macOS with AppleScript access.
- The app is designed to run continuously in the background.
