"""One clock for the whole app.

All times are stored as local wall-clock time in APP_TIMEZONE
(India by default), which is what users type into the forms. The
database session uses the same zone (see database.py), so Python
checks and SQL CURRENT_TIMESTAMP checks always agree, whatever
timezone the server itself runs in.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import APP_TIMEZONE


def now_local():
    """Current time in APP_TIMEZONE, without tzinfo (matches the DB columns)."""
    return datetime.now(ZoneInfo(APP_TIMEZONE)).replace(tzinfo=None)
