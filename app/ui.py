"""Shared look and feel: small building blocks every page uses.

Colours, fonts and sizes live in .streamlit/config.toml ([theme]). This
module says WHICH named colour each status gets, and holds the ONLY custom
CSS in the app (_CSS below): text sizes the theme cannot set, white cards
with a soft shadow, the page banner, coloured stat cards and the sidebar
highlight.

Building blocks:
    apply_style()        call once at the top of app.py
    page_header()        warm banner: icon, title, one line of purpose
    card()               white card with a soft shadow (use with `with`)
    grid()               lay cards out in rows that keep order on phones
    stat_card()          colourful card: icon + big number + label + button
    status_badge()       coloured label for a status (words, not colour alone)
    badge_markdown()     the same badge, for use inside st.markdown text
    empty_state()        icon + encouraging sentence + next-step button
    section_card()       a card with a title, to group related things
    centered_card()      a card in the middle of the page (sign-in)
    friendly_time()      "in 45 min", "2 hrs ago" (India time)
"""

from datetime import datetime
from itertools import count

import streamlit as st

from app.timeutil import now_local

# ---------------------------------------------------------------- statuses
# status -> (friendly words, theme colour, Material icon)
# Words always carry the meaning; colour and icon only help scanning.
# Note: in .streamlit/config.toml the "blue" slot is TEAL and "primary"
# is royal blue.

STATUS_STYLES = {
    # Donations
    "AVAILABLE": ("Available", "green", ":material/check_circle:"),
    "RESERVED": ("Reserved", "yellow", ":material/schedule:"),
    "PICKED_UP": ("Picked up", "blue", ":material/local_shipping:"),
    "DELIVERED": ("Delivered", "violet", ":material/task_alt:"),
    "EXPIRED": ("Expired", "red", ":material/error:"),
    # Pickup requests
    "REQUESTED": ("Waiting for volunteer", "yellow",
                  ":material/hourglass_top:"),
    "ACCEPTED": ("Volunteer assigned", "primary",
                 ":material/directions_walk:"),
    # Organizations and people
    "PENDING": ("Waiting for approval", "gray", ":material/hourglass_top:"),
    "VERIFIED": ("Verified", "green", ":material/verified:"),
    "REJECTED": ("Not approved", "red", ":material/block:"),
    "ACTIVE": ("Active", "green", ":material/check_circle:"),
    "DISABLED": ("Switched off", "gray", ":material/block:"),
    # Volunteers
    "BUSY": ("On a pickup", "blue", ":material/local_shipping:"),
    # Food urgency (from food_risk_service)
    "HIGH": ("Urgent", "red", ":material/priority_high:"),
    "MEDIUM": ("Soon", "yellow", ":material/schedule:"),
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


# ---------------------------------------------------------------- style
# The only custom CSS in the app. Colours match .streamlit/config.toml.

_CSS = """
<style>
/* Text sizes: labels and buttons 17px; nothing smaller than 15px. */
[data-testid="stWidgetLabel"] p { font-size: 17px; }
.stButton button p, .stFormSubmitButton button p, .stLinkButton a p,
.stPageLink a p, .stDownloadButton button p {
    font-size: 17px; font-weight: 600;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stMarkdownContainer"] small { font-size: 15px; }
/* Captions: darker than Streamlit's faded grey so they pass AA (7:1). */
[data-testid="stCaptionContainer"] { color: #4B5563; opacity: 1; }
[data-testid="stMetricLabel"] p { font-size: 17px; font-weight: 600; }
[data-testid="stSidebarNavLink"] span { font-size: 17px; }
[data-testid="stExpander"] summary p { font-size: 17px; font-weight: 600; }
[data-testid="stExpander"] details {
    background: #FFFFFF;
    box-shadow: 0 2px 10px rgba(31, 42, 55, .06);
}

/* Buttons: easy to tap, gentle lift on hover. Primary = royal blue:
   hover #3B5BDB, pressed #2B3FA0 (white text passes AA on all three). */
.stButton button, .stFormSubmitButton button, .stLinkButton a,
.stPageLink a, .stDownloadButton button {
    min-height: 2.6rem;
    transition: transform .15s ease, box-shadow .15s ease,
                background-color .15s ease;
}
.stButton button:hover, .stFormSubmitButton button:hover,
.stLinkButton a:hover, .stDownloadButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(54, 79, 199, .20);
}
[data-testid^="stBaseButton-primary"]:hover {
    background: #3B5BDB; border-color: #3B5BDB; color: #FFFFFF;
}
[data-testid^="stBaseButton-primary"]:active {
    background: #2B3FA0; border-color: #2B3FA0;
}

/* Cards and forms: white with a soft shadow; cards lift a little on hover. */
[class*="st-key-card-"], [class*="st-key-tone-"], [data-testid="stForm"] {
    background: #FFFFFF;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(31, 42, 55, .06);
}
[class*="st-key-card-"], [class*="st-key-tone-"] {
    transition: transform .15s ease, box-shadow .15s ease;
}
[class*="st-key-card-"]:hover, [class*="st-key-tone-"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(54, 79, 199, .12);
}

/* Stat cards: each in its own soft colour, with a coral accent stripe
   and coral icon (#F03E3E passes 3:1 on every tint). */
[class*="st-key-tone-"] { box-shadow: inset 0 4px 0 #FF6B6B,
                                      0 2px 10px rgba(31, 42, 55, .06); }
[class*="st-key-tone-royal"]  { background: #EDF2FF; }
[class*="st-key-tone-green"]  { background: #EBFBEE; }
[class*="st-key-tone-teal"]   { background: #E6FCF5; }
[class*="st-key-tone-purple"] { background: #F3F0FF; }
[class*="st-key-tone-coral"]  { background: #FFF0F0; }
[class*="st-key-tone-"] [data-testid="stMetricLabel"] span[role="img"] {
    color: #F03E3E;
}

/* Page banner: royal-blue gradient (never lighter, so white text passes),
   white title and text, light-coral icon and a coral stripe. */
[class*="st-key-banner-"] {
    background: linear-gradient(135deg, #364FC7 0%, #3B5BDB 100%);
    border-radius: 20px;
    padding: 1.1rem 1.4rem 1.1rem 1.6rem;
    margin-bottom: .5rem;
    box-shadow: inset 6px 0 0 #FF6B6B;
}
[class*="st-key-banner-"] h1 { padding: 0; }
[class*="st-key-banner-"], [class*="st-key-banner-"] * { color: #FFFFFF; }
[class*="st-key-banner-"] span[role="img"] { color: #FFA8A8; }

/* Sidebar menu: selected page royal blue with white text; hover #DBE4FF. */
[data-testid="stSidebarNavLink"] { border-radius: 12px; }
[data-testid="stSidebarNavLink"]:hover { background: #DBE4FF; }
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebarNavLink"][aria-current="page"]:hover {
    background: #364FC7;
}
[data-testid="stSidebarNavLink"][aria-current="page"] * { color: #FFFFFF; }

/* Phones: use the full width, keep a small margin. */
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding: 4.5rem 1rem 2rem 1rem;
    }
}
</style>
"""

# Card keys must be unique within one run; restarted by apply_style().
_counter = count()


def _key(prefix):
    return f"{prefix}-{next(_counter)}"


def apply_style():
    """Add the app's small style sheet. Call once, at the top of each run."""
    global _counter
    _counter = count()
    st.html(_CSS)


# ---------------------------------------------------------------- pieces

def page_header(title, purpose, icon=None):
    """Warm banner at the top of a page: icon, title, and one plain line
    saying what this page is for."""
    with st.container(key=_key("banner")):
        st.title(f"{icon} {title}" if icon else title)
        st.markdown(purpose)


def grid(items, per_row=2):
    """Yield (column, item) pairs row by row. On a phone the columns
    stack, and row-by-row keeps the cards in their original order."""
    for start in range(0, len(items), per_row):
        columns = st.columns(per_row)
        for column, item in zip(columns, items[start:start + per_row]):
            yield column, item


def card(tone=None):
    """A white card with a soft shadow. Use with `with`:

        with ui.card():
            st.markdown("**Vegetable biryani** · 20 kg")

    tone="royal" / "green" / "teal" / "purple" / "coral" gives a soft
    coloured card with a coral accent stripe (used for stat cards).
    """
    prefix = f"tone-{tone}" if tone else "card"
    return st.container(border=True, key=_key(prefix))


def _action(button_label, page=None, key=None, primary=False):
    """A full-width link to another page, or a button (True if clicked)."""
    if not button_label:
        return False
    if page is not None:
        st.page_link(page, label=button_label,
                     icon=":material/arrow_forward:", width="stretch")
        return False
    return st.button(button_label, key=key, width="stretch",
                     type="primary" if primary else "secondary")


def stat_card(label, value, caption=None, icon=None, tone="royal",
              button_label=None, page=None, key=None):
    """A colourful number card: icon + big number + label, with an optional
    button to the page where you act on it.

    Returns True when its button (not a page link) was clicked.
    """
    with card(tone):
        st.metric(f"{icon} {label}" if icon else label, value)
        if caption:
            st.caption(caption)
        return _action(button_label, page=page, key=key)


def empty_state(message, icon=":material/inbox:", hint=None,
                button_label=None, page=None, key=None):
    """Shown instead of an empty list: an icon, one encouraging sentence,
    and the next step. Returns True when its button (not a link) was clicked.
    """
    with card():
        st.markdown(f"## :orange[{icon}]")
        st.markdown(f"**{message}**")
        if hint:
            st.markdown(hint)
        return _action(button_label, page=page, key=key, primary=True)


def section_card(title=None, caption=None):
    """A card with a title that groups related things. Use with `with`:

        with section_card("Today's pickups"):
            st.write(...)
    """
    box = card()
    if title:
        box.subheader(title)
    if caption:
        box.caption(caption)
    return box


def centered_card(width=560):
    """A card in the middle of the page (sign-in screens). On a phone it
    simply fills the screen width. Use with `with`."""
    outer = st.container(horizontal_alignment="center")
    return outer.container(border=True, width=width, key=_key("card"))


# ---------------------------------------------------------------- time

def to_datetime(value):
    """A datetime from a datetime or an ISO string (None if missing)."""
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
    when = to_datetime(value)
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
    when = to_datetime(value)
    if when is None:
        return "—"
    hour = when.strftime("%I").lstrip("0")
    text = f"{when.day} {when.strftime('%b')}, {hour}:{when.strftime('%M')} " \
           f"{when.strftime('%p').lower()}"
    if when.year != now_local().year:
        text = text.replace(",", f" {when.year},", 1)
    return text
