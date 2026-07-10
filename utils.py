from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlparse


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_date_key(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


def format_display_date(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S")


def add_seconds(dt: datetime, seconds: float) -> datetime:
    return dt + timedelta(seconds=seconds)


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        return host[4:]
    return host or "unknown"
