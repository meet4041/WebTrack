from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from config import SUPPORTED_BROWSERS
from storage import LocalHistoryStore


@dataclass(frozen=True)
class BrowserSnapshot:
    browser: str
    title: str
    url: str
    captured_at: datetime


class BrowserTracker:
    def __init__(self, store: LocalHistoryStore, logger) -> None:
        self.store = store
        self.logger = logger
        self.state = self.store.load_state()
        self.sessions: list[dict[str, Any]] = self.state.get("sessions", [])
        self.active_session: dict[str, Any] | None = self.state.get("active_session")
        self._relink_active_session()
        self._refresh_active_duration(datetime.now())

    def poll(self) -> None:
        now = datetime.now()
        snapshot = self._get_active_snapshot(now)

        if snapshot is None:
            self._close_active(now)
            self._persist(now)
            return

        if self.active_session is None:
            self._start_new_session(snapshot)
            self._persist(now)
            return

        if self._matches_active(snapshot):
            if self._needs_day_rollover(now):
                boundary = self._split_active_session(now)
                self._start_new_session(BrowserSnapshot(snapshot.browser, snapshot.title, snapshot.url, boundary))
                self._refresh_active_duration(now)
                self._persist(now)
                return
            self._update_active_snapshot(snapshot)
            self._refresh_active_duration(now)
            self._persist(now)
            return

        self._close_active(snapshot.captured_at)
        self._start_new_session(snapshot)
        self._persist(now)

    def shutdown(self) -> None:
        now = datetime.now()
        self._close_active(now)
        self._persist(now)

    def _matches_active(self, snapshot: BrowserSnapshot) -> bool:
        return (
            self.active_session is not None
            and self.active_session["browser"] == snapshot.browser
            and self.active_session["url"] == snapshot.url
        )

    def _start_new_session(self, snapshot: BrowserSnapshot) -> None:
        self.active_session = {
            "browser": snapshot.browser,
            "title": snapshot.title,
            "url": snapshot.url,
            "start_iso": snapshot.captured_at.isoformat(),
            "end_iso": None,
            "duration_seconds": 0.0,
            "status": "ACTIVE",
        }
        self.sessions.append(self.active_session)
        self.logger.info("Started session %s %s", snapshot.browser, snapshot.url)

    def _update_active_snapshot(self, snapshot: BrowserSnapshot) -> None:
        if self.active_session is None:
            return
        self.active_session["title"] = snapshot.title
        self.active_session["url"] = snapshot.url
        self.active_session["status"] = "ACTIVE"

    def _refresh_active_duration(self, now: datetime) -> None:
        if self.active_session is None:
            return
        start_dt = datetime.fromisoformat(self.active_session["start_iso"])
        self.active_session["duration_seconds"] = max(0.0, (now - start_dt).total_seconds())

    def _needs_day_rollover(self, now: datetime) -> bool:
        if self.active_session is None:
            return False
        start_dt = datetime.fromisoformat(self.active_session["start_iso"])
        return start_dt.date() != now.date()

    def _split_active_session(self, now: datetime) -> datetime:
        if self.active_session is None:
            return now
        start_dt = datetime.fromisoformat(self.active_session["start_iso"])
        boundary = datetime.combine(now.date(), time.min)
        if boundary <= start_dt:
            return now
        self._close_active(boundary)
        return boundary

    def _close_active(self, end_time: datetime) -> None:
        if self.active_session is None:
            return
        start_dt = datetime.fromisoformat(self.active_session["start_iso"])
        duration = max(0.0, (end_time - start_dt).total_seconds())
        self.active_session["end_iso"] = end_time.isoformat()
        self.active_session["duration_seconds"] = duration
        self.active_session["status"] = "COMPLETED"
        self.logger.info("Closed session %s %s", self.active_session["browser"], self.active_session["url"])
        self.active_session = None

    def _persist(self, generated_at: datetime) -> None:
        state = {
            "sessions": self.sessions,
            "active_session": self.active_session,
        }
        self.store.save_state(state)
        self._refresh_daily_files(generated_at)

    def _refresh_daily_files(self, generated_at: datetime) -> None:
        by_day: dict[str, list[dict[str, Any]]] = {}
        for session in self.sessions:
            start_dt = datetime.fromisoformat(session["start_iso"])
            by_day.setdefault(start_dt.date().isoformat(), []).append(session)

        for day_key, day_sessions in by_day.items():
            day_dt = datetime.fromisoformat(f"{day_key}T00:00:00")
            self.store.render_day_file(day_dt, day_sessions, generated_at)

    def _relink_active_session(self) -> None:
        if self.active_session is None:
            return
        for session in reversed(self.sessions):
            if (
                session.get("start_iso") == self.active_session.get("start_iso")
                and session.get("browser") == self.active_session.get("browser")
                and session.get("url") == self.active_session.get("url")
            ):
                session.update(self.active_session)
                self.active_session = session
                return
        self.sessions.append(self.active_session)

    def _get_active_snapshot(self, captured_at: datetime) -> BrowserSnapshot | None:
        script = r'''
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true
end tell

if frontApp is not "Google Chrome" and frontApp is not "Safari" then
    return "NONE"
end if

if frontApp is "Google Chrome" then
    tell application "Google Chrome"
        if not running then return "NONE"
        if (count of windows) = 0 then return "NONE"
        set activeTab to active tab of front window
        return "Google Chrome" & linefeed & (title of activeTab) & linefeed & (URL of activeTab)
    end tell
end if

if frontApp is "Safari" then
    tell application "Safari"
        if not running then return "NONE"
        if (count of windows) = 0 then return "NONE"
        set activeTab to current tab of front window
        return "Safari" & linefeed & (name of activeTab) & linefeed & (URL of activeTab)
    end tell
end if

return "NONE"
'''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            self.logger.error("osascript not available")
            return None

        output = result.stdout.strip()
        if not output or output == "NONE":
            return None

        parts = output.splitlines()
        if len(parts) < 3:
            return None

        browser, title, url = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if browser not in SUPPORTED_BROWSERS or not url:
            return None

        return BrowserSnapshot(browser=browser, title=title or url, url=url, captured_at=captured_at)
