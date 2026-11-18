"""Settings lookup.

Order: environment variables (and a local .env file), then Streamlit
secrets. Nothing secret is ever stored in the code.

Why the snapshot below matters: the first time Streamlit reads
secrets.toml it COPIES each top-level secret into os.environ,
overwriting what was there. Without the snapshot, a TEST_DATABASE_URL
that the tests put into DATABASE_URL would silently be replaced by the
real database address from secrets.toml, and the tests (which empty
every table) would run against the real data.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Environment as it was when the app started, before Streamlit secrets
# could overwrite it. These values win over secrets.toml.
_STARTUP_ENV = dict(os.environ)


def _empty(value):
    return value in (None, "")


def _from_secrets(name):
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        # No secrets file, or not running inside Streamlit.
        pass
    return None


def get_setting(name, default=None):
    startup = _STARTUP_ENV.get(name)
    if not _empty(startup):
        current = os.getenv(name)
        # Code may change a setting on purpose after start-up (tests do).
        # Use that, unless it is just Streamlit copying in the secret.
        if (not _empty(current) and current != startup
                and current != _from_secrets(name)):
            return current
        return startup

    value = os.getenv(name)
    if not _empty(value):
        return value

    secret = _from_secrets(name)
    return default if secret is None else secret


def get_list_setting(name):
    """A comma-separated setting (or a list in secrets.toml) as a list."""
    value = get_setting(name, "")
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(",")
    return [item.strip() for item in items if str(item).strip()]


APP_TIMEZONE = get_setting("APP_TIMEZONE", "Asia/Kolkata")
