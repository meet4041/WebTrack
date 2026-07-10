from __future__ import annotations

import signal
import time

from browser_tracker import BrowserTracker
from config import POLL_INTERVAL_SECONDS
from logger import setup_logging
from storage import LocalHistoryStore


def main() -> None:
    logger = setup_logging()
    store = LocalHistoryStore()
    tracker = BrowserTracker(store, logger)
    running = True

    def stop(_signum, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    logger.info("WebTrack started")
    try:
        while running:
            try:
                tracker.poll()
            except Exception:
                logger.exception("Polling failed")
            time.sleep(POLL_INTERVAL_SECONDS)
    finally:
        tracker.shutdown()
        logger.info("WebTrack stopped")


if __name__ == "__main__":
    main()
