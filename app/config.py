"""Settings lookup.

Order: environment variables (and a local .env file), then Streamlit
secrets. Nothing secret is ever stored in the code.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=None):
    value = os.getenv(name)
    if value not in (None, ""):
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        # No secrets file, or not running inside Streamlit.
        pass

    return default


def get_list_setting(name):
    """A comma-separated setting (or a list in secrets.toml) as a list."""
    value = get_setting(name, "")
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(",")
    return [item.strip() for item in items if str(item).strip()]


APP_TIMEZONE = get_setting("APP_TIMEZONE", "Asia/Kolkata")
