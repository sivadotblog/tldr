"""
Remove archived newsletters older than the retention window.
"""

import os
import re
from datetime import datetime

RETENTION_MONTHS = 18
CATEGORIES = ["ai", "data", "devops", "infosec", "tech"]
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def cutoff_date():
    today = datetime.utcnow()
    year = today.year
    month = today.month - RETENTION_MONTHS
    while month <= 0:
        month += 12
        year -= 1
    day = min(today.day, 28)  # avoid invalid dates when shifting across months
    return datetime(year, month, day)


def purge():
    cutoff = cutoff_date()
    removed = []
    for category in CATEGORIES:
        directory = os.path.join("tldr", category)
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            match = DATE_RE.match(filename)
            if not match:
                continue
            file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
            if file_date < cutoff:
                path = os.path.join(directory, filename)
                os.remove(path)
                removed.append(path)
    return removed


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    cutoff = cutoff_date()
    logging.info(f"Purging newsletters older than {cutoff.strftime('%Y-%m-%d')} ({RETENTION_MONTHS} months)")
    removed = purge()
    logging.info(f"Removed {len(removed)} newsletter file(s)")
    for path in removed:
        logging.info(f" - {path}")
