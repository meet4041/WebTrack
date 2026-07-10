from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config import HISTORY_DIR, STATE_DIR, STATE_FILE
from utils import domain_from_url, format_date_key, format_duration, format_time


class LocalHistoryStore:
    def __init__(self) -> None:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> dict[str, Any]:
        if not STATE_FILE.exists():
            return {"sessions": [], "active_session": None}
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"sessions": [], "active_session": None}

    def save_state(self, state: dict[str, Any]) -> None:
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=True), encoding="utf-8")

    def render_day_file(self, day: datetime, sessions: list[dict[str, Any]], generated_at: datetime) -> Path:
        year_dir = HISTORY_DIR / day.strftime("%Y")
        month_dir = year_dir / day.strftime("%B")
        month_dir.mkdir(parents=True, exist_ok=True)

        file_path = month_dir / f"{format_date_key(day)}.txt"
        file_path.write_text(self._render_content(day, sessions, generated_at), encoding="utf-8")
        return file_path

    def _render_content(self, day: datetime, sessions: list[dict[str, Any]], generated_at: datetime) -> str:
        lines: list[str] = [f"Date: {format_date_key(day)}", ""]

        ordered_sessions = sorted(sessions, key=lambda item: item["start_iso"])
        for session in ordered_sessions:
            start_dt = datetime.fromisoformat(session["start_iso"])
            end_iso = session.get("end_iso")
            end_dt = datetime.fromisoformat(end_iso) if end_iso else None
            duration = self._effective_duration(session, generated_at)
            lines.extend(
                [
                    "---",
                    f"Date: {format_date_key(start_dt)}",
                    f"Browser: {session['browser']}",
                    f"Title: {session['title']}",
                    f"URL: {session['url']}",
                    f"Start Time: {format_time(start_dt)}",
                    f"End Time: {format_time(end_dt) if end_dt else '-'}",
                    f"Duration: {format_duration(duration)}",
                    f"Status: {session['status']}",
                    "",
                ]
            )

        lines.extend(self._render_summary(ordered_sessions, generated_at))
        return "\n".join(lines).rstrip() + "\n"

    def _render_summary(self, sessions: list[dict[str, Any]], generated_at: datetime) -> list[str]:
        total_seconds = sum(self._effective_duration(item, generated_at) for item in sessions)
        browser_seconds = Counter()
        domain_seconds = defaultdict(float)
        domain_visits = Counter()

        for session in sessions:
            duration = self._effective_duration(session, generated_at)
            browser_seconds[session["browser"]] += duration
            domain = domain_from_url(session["url"])
            domain_seconds[domain] += duration
            domain_visits[domain] += 1

        top_domains = sorted(domain_visits.keys(), key=lambda dom: (-domain_visits[dom], -domain_seconds[dom], dom))[:10]

        lines = [
            "Today's Summary",
            "",
            f"Total Websites Visited: {len(sessions)}",
            f"Chrome Usage: {format_duration(browser_seconds.get('Google Chrome', 0))}",
            f"Safari Usage: {format_duration(browser_seconds.get('Safari', 0))}",
            f"Total Browsing Time: {format_duration(total_seconds)}",
            "",
            "Top Domains",
            "",
        ]
        for domain in top_domains:
            lines.append(f"{domain} — {format_duration(domain_seconds[domain])}")
        if not top_domains:
            lines.append("No browsing activity recorded yet.")
        return lines

    def _effective_duration(self, session: dict[str, Any], now: datetime) -> float:
        if session.get("status") == "ACTIVE" or session.get("end_iso") is None:
            start_dt = datetime.fromisoformat(session["start_iso"])
            return max(0.0, (now - start_dt).total_seconds())
        return float(session.get("duration_seconds", 0))
