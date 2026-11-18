"""Shared look and feel: small building blocks every page uses.

Colours live in .streamlit/config.toml ([theme]). This module only says
WHICH named colour each status gets, plus a few lines of CSS for things
the theme cannot do (bigger tap targets, tighter phone margins).

Building blocks:
    apply_style()        call once at the top of app.py
    page_header()        title + one line saying what the page is for
    stat_card()          a number in a card, with an optional button
    status_badge()       coloured label for a status (text, not colour alone)
    badge_markdown()     the same badge, for use inside st.markdown text
    empty_state()        "nothing here yet" + what to do next
    section_card()       a rounded card to group related things
    friendly_time()      "in 45 min", "2 hrs ago" (India time)
"""

from datetime import datetime

import streamlit as st

from app.timeutil import now_local

# ---------------------------------------------------------------- statuses
# status -> (friendly words, theme colour, Material icon)
# Words always carry the meaning; colour and icon only help scanning.

STATUS_STYLES = {
    # Donations
    "AVAILABLE": ("Available", "green", ":material/check_circle:"),
    "RESERVED": ("Reserved", "yellow", ":material/schedule:"),
    "PICKED_UP": ("Picked up", "blue", ":material/local_shipping:"),
    "DELIVERED": ("Delivered", "gray", ":material/task_alt:"),
    "EXPIRED": ("Expired", "red", ":material/error:"),
    # Pickup requests
    "REQUESTED": ("Waiting for volunteer", "yellow", ":material/hourglass_top:"),
    "ACCEPTED": ("Volunteer assigned", "violet", ":material/directions_walk:"),
    # Organizations and people
    "PENDING": ("Waiting for approval", "yellow", ":material/hourglass_top:"),
    "VERIFIED": ("Verified", "green", ":material/verified:"),
    "REJECTED": ("Not approved", "red", ":material/block:"),
    "ACTIVE": ("Active", "green", ":material/check_circle:"),
    "DISABLED": ("Switched off", "gray", ":material/block:"),
    # Volunteers
    "BUSY": ("On a pickup", "blue", ":material/local_shipping:"),
    # Food urgency (from food_risk_service)
    "HIGH": ("Urgent", "red", ":material/priority_high:"),
    "MEDIUM": ("Soon", "orange", ":material/schedule:"),
    "LOW": ("Plenty of time", "green", ":material/check_circle:"),
}

_UNKNOWN_STYLE = ("", "gray", ":material/help:")


def status_style(status):
    """(words, colour, icon) for a status code like 'PICKED_UP'."""
    code = str(status or "").upper()
    words, colour, icon = STATUS_STYLES.get(code, _UNKNOWN_STYLE)
    return (words or code.replace("_", " ").capitalize() or "Unknown",
            colour, icon)


def status_badge(status):
    """Show a status as a small coloured label with words and an icon."""
    words, colour, icon = status_style(status)
    st.badge(words, icon=icon, color=colour)


def badge_markdown(status):
    """The same badge as text, to put inside st.markdown(...)."""
    words, colour, icon = status_style(status)
    return f":{colour}-badge[{icon} {words}]"


# ---------------------------------------------------------------- layout

_CSS = """
<style>
/* Easy-to-tap buttons and links (about 44px, the size of a fingertip). */
.stButton button, .stFormSubmitButton button,
.stDownloadButton button, .stLinkButton a, .stPageLink a {
    min-height: 2.75rem;
}
/* Phones: use the full width, keep a small margin. */
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 2.5rem;
    }
}
</style>
"""


def apply_style():
    """Add the few style rules the theme cannot express. Call once per run."""
    st.html(_CSS)


def page_header(title, purpose, icon=None):
    """Page title plus one plain sentence saying what to do here."""
    st.title(f"{icon} {title}" if icon else title)
    st.markdown(purpose)


def _action(button_label, page=None, key=None, primary=False):
    """A full-width link to another page, or a button (returns True if clicked)."""
    if not button_label:
        return False
    if page is not None:
        st.page_link(page, label=button_label, icon=":material/arrow_forward:",
                     width="stretch")
        return False
    return st.button(button_label, key=key, width="stretch",
                     type="primary" if primary else "secondary")


def stat_card(label, value, caption=None, icon=None,
              button_label=None, page=None, key=None):
    """A number in a card, e.g. 'Food available: 12', with an optional
    button that takes you to the page where you act on it.

    Returns True when its button (not a page link) was clicked.
    """
    with st.container(border=True):
        st.metric(f"{icon} {label}" if icon else label, value)
        if caption:
            st.caption(caption)
        return _action(button_label, page=page, key=key)


def empty_state(message, icon=":material/inbox:", hint=None,
                button_label=None, page=None, key=None):
    """Shown instead of an empty list: what is missing and what to do next.

    Returns True when its button (not a page link) was clicked.
    """
    with st.container(border=True):
        st.markdown(f"### {icon}")
        st.markdown(f"**{message}**")
        if hint:
            st.markdown(hint)
        return _action(button_label, page=page, key=key, primary=True)


def section_card(title=None, caption=None):
    """A rounded card that groups related things. Use with `with`:

        with section_card("Today's pickups"):
            st.write(...)
    """
    box = st.container(border=True)
    if title:
        box.subheader(title)
    if caption:
        box.caption(caption)
    return box


# ---------------------------------------------------------------- time

def _to_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value)).replace(tzinfo=None)
    except ValueError:
        return None


def _plural(number, word):
    return f"{number} {word}" + ("" if number == 1 else "s")


def friendly_time(value, now=None):
    """'in 45 min', '2 hrs ago', 'just now'; older or later times as a date.

    All times are India time (see app/timeutil.py).
    """
    when = _to_datetime(value)
    if when is None:
        return "—"
    now = now or now_local()
    seconds = (when - now).total_seconds()
    minutes = int(abs(seconds) // 60)

    if minutes < 1:
        return "just now"
    if minutes < 60:
        amount = f"{minutes} min"
    elif minutes < 24 * 60:
        hours = minutes // 60
        amount = _plural(hours, "hr")
    else:
        return clock_time(when)
    return f"in {amount}" if seconds > 0 else f"{amount} ago"


def clock_time(value):
    """'18 Nov, 3:30 pm'. Shows the year only when it is not this year."""
    when = _to_datetime(value)
    if when is None:
        return "—"
    hour = when.strftime("%I").lstrip("0")
    text = f"{when.day} {when.strftime('%b')}, {hour}:{when.strftime('%M')} " \
           f"{when.strftime('%p').lower()}"
    if when.year != now_local().year:
        text = text.replace(",", f" {when.year},", 1)
    return text
