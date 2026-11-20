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

import base64
import functools
import html
import re
import zlib
from datetime import datetime
from itertools import count
from pathlib import Path

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
    "REQUESTED": ("Waiting to be accepted", "yellow",
                  ":material/hourglass_top:"),
    "ACCEPTED": ("Accepted", "primary", ":material/thumb_up:"),
    # Shown instead of ACCEPTED, depending on whether a volunteer is set
    # (see pickup_status below). Not stored in the database.
    "NEEDS_VOLUNTEER": ("Needs a volunteer", "yellow",
                        ":material/person_search:"),
    "ASSIGNED": ("Volunteer assigned", "primary",
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


def pickup_status(status, volunteer_id):
    """What a pickup's badge should say: an accepted pickup either still
    needs a volunteer or has one."""
    if status == "ACCEPTED":
        return "ASSIGNED" if volunteer_id else "NEEDS_VOLUNTEER"
    return status


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
    box-shadow: 0 12px 28px rgba(54, 79, 199, .18);
}

/* Stat cards: WHITE, so colour comes only from each card's own top
   stripe and icon circle. Rule of thumb: one strong gradient block per
   page (the Home impact strip); everything else light. */
[class*="st-key-tone-"] {
    background: #FFFFFF;
    --stripe: #364FC7;
    box-shadow: inset 0 4px 0 var(--stripe), 0 2px 10px rgba(31, 42, 55, .06);
}
[class*="st-key-tone-"]:hover {
    box-shadow: inset 0 4px 0 var(--stripe), 0 12px 28px rgba(54, 79, 199, .18);
}
[class*="st-key-tone-royal"]  { --stripe: #364FC7; }
[class*="st-key-tone-green"]  { --stripe: #2B8A3E; }
[class*="st-key-tone-teal"]   { --stripe: #0CA678; }
[class*="st-key-tone-purple"] { --stripe: #7048E8; }
[class*="st-key-tone-coral"]  { --stripe: #FF6B6B; }
[class*="st-key-tone-red"]    { --stripe: #E03131; }
[class*="st-key-tone-amber"]  { --stripe: #F59F00; }

/* Stat cards (stat_card): compact. Icon + label on one line, the number
   big and bold below in the card's own colour (all 5.4:1 or more on
   white), then a short hint and link. */
[class*="-stat-"] { padding: .8rem .9rem .55rem; gap: .2rem; }
[class*="-stat-"] [data-testid="stMetricLabel"] p { font-size: 16px; }
[class*="-stat-"] [data-testid="stMetricLabel"] span[role="img"] {
    width: 1.9em; height: 1.9em; line-height: 1.9em; margin-right: .35em;
}
[class*="-stat-"] [data-testid="stMetricValue"],
[class*="-stat-"] [data-testid="stMetricValue"] * {
    font-family: "Poppins", sans-serif; font-weight: 700;
    font-size: 2.1rem; line-height: 1.15; color: var(--number, #364FC7);
}
/* Labels wrap instead of being cut off ("Food availa..."). */
[class*="-stat-"] [data-testid="stMetricLabel"],
[class*="-stat-"] [data-testid="stMetricLabel"] * {
    white-space: normal; overflow: visible; text-overflow: clip;
}
[class*="-stat-"] [data-testid="stCaptionContainer"] p {
    margin: 0 0 .25rem; line-height: 1.35;
}
[class*="-stat-"] .stPageLink a { min-height: 2.5rem; padding-left: 0; }
/* Cards in one row are the same height. */
[class*="st-key-statrow"] [data-testid="stColumn"] [data-testid="stLayoutWrapper"] {
    flex: 1 1 auto;
}
[class*="st-key-statrow"] [class*="-stat-"] { height: 100%; }
/* The hint and link sit at the bottom of the card. */
[class*="-stat-"] > :nth-child(2) { margin-top: auto; }
[class*="st-key-tone-green-stat"]  { --number: #237032; }
[class*="st-key-tone-red-stat"]    { --number: #C92A2A; }
[class*="st-key-tone-amber-stat"]  { --number: #9C5400; }
[class*="st-key-tone-purple-stat"] { --number: #6741D9; }
[class*="st-key-tone-teal-stat"]   { --number: #0B7A5B; }
[class*="st-key-tone-coral-stat"]  { --number: #C92A2A; }

/* Quick actions (admin Home): small outlined pill buttons. */
[class*="st-key-quick-actions"] { flex-wrap: wrap; gap: .5rem; }
[class*="st-key-quick-actions"] .stButton button {
    min-height: 2.5rem; border-radius: 999px; padding: .2rem 1rem;
    background: #FFFFFF; border: 1.5px solid #364FC7;
}
[class*="st-key-quick-actions"] .stButton button * {
    color: #2B3FA0; font-size: 16px;
}
[class*="st-key-quick-actions"] .stButton button:hover {
    background: #EDF2FF;
}

/* Getting started checklist (admin Home, before the first delivery).
   Ticks green (6.1:1), the next step highlighted, words always shown. */
.fr-progress {
    height: 10px; border-radius: 999px; background: #E9ECEF;
    overflow: hidden; margin: .1rem 0 .3rem;
}
.fr-progress > div { height: 100%; border-radius: 999px; background: #364FC7; }
[class*="st-key-step-done"] [data-testid="stIconMaterial"] {
    color: #237032 !important;
}
[class*="st-key-step-next"] .stPageLink a {
    background: #EDF2FF; border-radius: 10px;
}
[class*="st-key-step-next"] .stPageLink a p { font-weight: 700; }
[class*="st-key-step-next"] [data-testid="stIconMaterial"] {
    color: #C92A2A !important;
}

/* Page banner: LIGHT. White to very light lavender with a faint coral
   tint at the far right, dark slate text (13:1), royal-blue icon (6:1),
   thin coral stripe, soft shadow. */
[class*="st-key-banner-"] {
    background: linear-gradient(100deg, #FFFFFF 0%, #EEF2FF 72%, #FFF0F0 100%);
    border-radius: 20px;
    padding: 1rem 1.4rem 1rem 1.6rem;
    margin-bottom: .5rem;
    box-shadow: inset 4px 0 0 #FF6B6B, 0 4px 18px rgba(31, 42, 55, .07);
}
[class*="st-key-banner-"] h1 { padding: 0; }
[class*="st-key-banner-"], [class*="st-key-banner-"] * { color: #1F2A37; }
[class*="st-key-banner-"] span[role="img"] { color: #364FC7; }

/* ---- Sidebar: dark navy dashboard menu ------------------------------
   Contrast on the LIGHTER end of the gradient (#2B3FA0, worst case):
   menu text white 85% 7.0:1, selected 6.3:1, labels #BAC8FF 5.5:1,
   coral pill text 5.2:1, light-coral selected bar #FFA8A8 3.4:1. */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E2A78 0%, #2B3FA0 100%);
}
/* Profile card at the bottom: the content becomes a column. */
[data-testid="stSidebarContent"] {
    display: flex; flex-direction: column; min-height: 100%;
}
[data-testid="stSidebarUserContent"] {
    margin-top: auto; padding-bottom: 1.5rem;
}

/* Menu links: white at 85%, hover = faint white overlay. */
[data-testid="stSidebarNavLink"] {
    border-radius: 10px; color: rgba(255, 255, 255, .85);
}
[data-testid="stSidebarNavLink"] * { color: rgba(255, 255, 255, .85); }
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255, 255, 255, .08);
}
[data-testid="stSidebarNavLink"]:hover * { color: #FFFFFF; }
/* Selected page: faint white highlight, light-coral bar on the left,
   white bold text. */
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebarNavLink"][aria-current="page"]:hover {
    background: rgba(255, 255, 255, .14);
    box-shadow: inset 4px 0 0 #FFA8A8;
}
[data-testid="stSidebarNavLink"][aria-current="page"] * {
    color: #FFFFFF; font-weight: 700;
}
/* Section labels (Food, People, Ministry). */
[data-testid="stNavSectionHeader"] {
    margin-top: 1.1rem; text-transform: uppercase;
    letter-spacing: .08em; font-size: 14px; font-weight: 700;
}
[data-testid="stNavSectionHeader"] * { color: #BAC8FF; font-size: 14px; }
/* Dividers: white at low opacity. The profile card has its own line,
   so Streamlit's line under the menu is not needed. */
[data-testid="stSidebarNavSeparator"] { display: none; }
[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, .2); }
/* Brand: bigger logo, ministry name and tagline (see brand()). */
[data-testid="stSidebarHeader"] { height: auto; min-height: 4.5rem; }

/* Profile card. */
.fr-profile { display: flex; gap: .7rem; align-items: center; }
.fr-profile .fr-avatar { width: 42px; height: 42px; font-size: 16px; }
.fr-profile-name {
    font-family: "Poppins", sans-serif; font-weight: 600; font-size: 16px;
    color: #FFFFFF; line-height: 1.3;
}
.fr-profile-role {
    display: inline-block; margin-top: .2rem; padding: .05rem .6rem;
    border-radius: 999px; background: rgba(255, 255, 255, .14);
    color: #FFFFFF; font-size: 15px;
}
[class*="st-key-profile"] {
    border-top: 1px solid rgba(255, 255, 255, .2); padding-top: .9rem;
}
[class*="st-key-profile"] .stButton button {
    background: transparent; border: 1px solid rgba(255, 255, 255, .35);
    min-height: 2.5rem;
}
[class*="st-key-profile"] .stButton button:hover {
    background: rgba(255, 255, 255, .08); box-shadow: none;
}
[class*="st-key-profile"] .stButton button * { color: #FFFFFF; }
[class*="st-key-profile"] [data-testid="stCaptionContainer"] a {
    color: #BAC8FF;
}

/* Small things people tap: the "?" help icons and caption links. */
[data-testid="stTooltipIcon"] button, [data-testid="stTooltipIcon"] > div {
    min-width: 32px; min-height: 32px;
    display: inline-flex; align-items: center; justify-content: center;
}
[data-testid="stCaptionContainer"] a { display: inline-block; padding: 12px 0; }
[data-testid="stRadio"] label { min-height: 40px; align-items: center; }

/* Page background: a soft blue glow at the top, behind everything.
   Its darkest point (#E7EDFF) still gives text 12:1 and links 5.8:1. */
[data-testid="stApp"] {
    background: linear-gradient(180deg, #E7EDFF 0, #F8F9FF 380px) fixed;
}
[data-testid="stHeader"] { background: transparent; }

/* Icons in soft tinted circles: stat cards, section titles, card titles.
   Each icon colour passes 3:1 on its circle. */
[class*="st-key-tone-"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-"] h3 span[role="img"],
[class*="st-key-ctitle-"] h4 span[role="img"] {
    /* Streamlit sets inline display/vertical-align on icons, so centre
       the glyph with line-height and override the alignment. */
    width: 2.1em; height: 2.1em; line-height: 2.1em; text-align: center;
    border-radius: 50%; margin-right: .45em;
    vertical-align: middle !important;
}
[class*="st-key-tone-royal"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-blue"] h3 span[role="img"],
[class*="st-key-ctitle-blue"] h4 span[role="img"] {
    background: #DBE4FF; color: #364FC7;
}
[class*="st-key-tone-coral"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-coral"] h3 span[role="img"],
[class*="st-key-ctitle-coral"] h4 span[role="img"] {
    background: #FFE3E3; color: #E03131;
}
[class*="st-key-tone-green"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-green"] h3 span[role="img"],
[class*="st-key-ctitle-green"] h4 span[role="img"] {
    background: #D3F9D8; color: #2B8A3E;
}
[class*="st-key-tone-purple"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-purple"] h3 span[role="img"],
[class*="st-key-ctitle-purple"] h4 span[role="img"] {
    background: #E5DBFF; color: #6741D9;
}
[class*="st-key-tone-red"] [data-testid="stMetricLabel"] span[role="img"] {
    background: #FFE3E3; color: #E03131;
}
[class*="st-key-tone-amber"] [data-testid="stMetricLabel"] span[role="img"] {
    background: #FFF3BF; color: #9C5400;
}
[class*="st-key-tone-teal"] [data-testid="stMetricLabel"] span[role="img"],
[class*="st-key-section-teal"] h3 span[role="img"],
[class*="st-key-ctitle-teal"] h4 span[role="img"] {
    background: #C3FAE8; color: #0B7A5B;
}

/* Section titles: a short coral underline. */
[class*="st-key-section-"] h3 { padding-bottom: .2rem; }
[class*="st-key-section-"] h3::after {
    content: ""; display: block; width: 56px; height: 4px;
    margin-top: .5rem; border-radius: 2px; background: #FF6B6B;
}

/* Brand at the top of the sidebar: logo mark (+ name, see brand()). */
[data-testid="stSidebarHeader"] { align-items: center; }
[data-testid="stSidebarLogo"] { height: 2.6rem; width: auto; }

/* Illustrations: centred, never wider than the screen. */
.fr-illustration { max-width: 100%; margin: 0 auto; }
.fr-illustration img { display: block; width: 100%; height: auto; }

/* People and organizations: initials avatar, name and small chips. */
.fr-person { display: flex; gap: .8rem; align-items: center; }
.fr-avatar {
    flex: 0 0 auto; width: 48px; height: 48px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: "Poppins", sans-serif; font-weight: 700; font-size: 18px;
}
.fr-name {
    font-family: "Poppins", sans-serif; font-weight: 700; font-size: 19px;
    color: #1F2A37; line-height: 1.3;
}
.fr-chips { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .3rem; }
.fr-chip {
    background: #EDF2FF; color: #1F2A37; border-radius: 999px;
    padding: .1rem .7rem; font-size: 15px;
}

/* Pickup progress: done steps blue, the current step coral. */
.fr-track { display: flex; list-style: none; margin: .5rem 0 .3rem; padding: 0; }
.fr-step {
    flex: 1; position: relative; display: flex; flex-direction: column;
    align-items: center; text-align: center; font-size: 15px;
    color: #4B5563; line-height: 1.2;
}
.fr-step::before {
    content: ""; position: absolute; top: 12px; right: 50%; width: 100%;
    height: 4px; background: #DEE2E6; z-index: 0;
}
.fr-step:first-child::before { display: none; }
.fr-step.done::before, .fr-step.current::before { background: #364FC7; }
.fr-dot {
    position: relative; z-index: 1; width: 28px; height: 28px; border-radius: 50%;
    border: 3px solid #868E96; background: #FFFFFF; color: #4B5563;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; box-sizing: border-box;
}
.fr-step.done .fr-dot { background: #364FC7; border-color: #364FC7; color: #FFFFFF; }
.fr-step.current .fr-dot {
    background: #F03E3E; border-color: #F03E3E; color: #FFFFFF;
    box-shadow: 0 0 0 5px #FFE3E3;
}
.fr-step.current { color: #1F2A37; font-weight: 700; }
.fr-label { margin-top: .4rem; }

/* Impact strip: the ONE vivid block on the page. Diagonal royal blue ->
   indigo -> violet, with a faint shine in the top-right corner.
   Worst case (violet end under the shine): white 5.4:1, labels 4.8:1.
   (The violet end is #6741D9, a touch deeper than #7048E8, so the labels
   pass AA everywhere.) */
.fr-impact {
    background:
        radial-gradient(circle at 100% 0%, rgba(255, 255, 255, .08) 0,
                        rgba(255, 255, 255, 0) 240px),
        linear-gradient(135deg, #364FC7 0%, #4C3BCF 55%, #6741D9 100%);
    border-radius: 18px; padding: 1.2rem 1.4rem 1.4rem; color: #FFFFFF;
    box-shadow: 0 10px 28px rgba(76, 59, 207, .35);
}
.fr-impact-line {
    font-family: "Poppins", sans-serif; font-weight: 600; font-size: 20px;
    margin: 0 0 .9rem;
}
.fr-impact-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem;
}
.fr-num {
    font-family: "Poppins", sans-serif; font-weight: 700; font-size: 34px;
    line-height: 1.1; animation: fr-pop .7s ease-out both;
}
.fr-stat:nth-child(2) .fr-num { animation-delay: .1s; }
.fr-stat:nth-child(3) .fr-num { animation-delay: .2s; }
.fr-stat:nth-child(4) .fr-num { animation-delay: .3s; }
.fr-num-label { font-size: 15px; color: #F3F0FF; }
@keyframes fr-pop {
    from { opacity: 0; transform: translateY(8px) scale(.9); }
    to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
    .fr-num { animation: none; }
    [class*="st-key-card-"], [class*="st-key-tone-"] { transition: none; }
}

/* Less empty space above the first banner (Streamlit's default is
   6rem). Phones keep room for the menu button at the top. */
[data-testid="stMainBlockContainer"] { padding-top: 2.5rem; }

/* Phones: use the full width, keep a small margin. */
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding: 3.75rem 1rem 2rem 1rem;
    }
    .fr-impact-grid { grid-template-columns: repeat(2, 1fr); }
    /* Stat cards: two per row instead of one long column. */
    [class*="st-key-statrow"] [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap; gap: .6rem;
    }
    [class*="st-key-statrow"] [data-testid="stColumn"] {
        flex: 1 1 calc(50% - .3rem) !important;
        width: calc(50% - .3rem) !important;
        min-width: calc(50% - .3rem) !important;
    }
    [class*="-stat-"] { padding: .7rem .7rem .45rem; }
    [class*="-stat-"] [data-testid="stMetricLabel"] p { font-size: 15px; }
    [class*="-stat-"] [data-testid="stMetricValue"],
    [class*="-stat-"] [data-testid="stMetricValue"] * { font-size: 1.8rem; }
    /* The banner picture is decoration: hide it on small screens. */
    [class*="st-key-banner-"] .fr-illustration { display: none; }
}
</style>
"""

# Pictures (simple flat SVGs, royal blue with coral accents).
ASSETS = Path(__file__).resolve().parent / "assets"

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

def page_header(title, purpose, icon=None, image=None):
    """Warm banner at the top of a page: icon, title, and one plain line
    saying what this page is for. `image` adds an illustration on the
    right (hidden on phones)."""
    with st.container(key=_key("banner")):
        if image:
            text, picture = st.columns([5, 2], vertical_alignment="center")
            with picture:
                illustration(image, width=190)
        else:
            text = st.container()
        with text:
            st.title(f"{icon} {title}" if icon else title)
            st.markdown(purpose)


def _css_text(text):
    """Text that is safe inside a CSS content: "..." string."""
    return "".join(ch for ch in str(text) if ch not in '\\"<>{}')


def brand(ministry_name, tagline):
    """Logo mark, ministry name and a one-line tagline at the top of the
    sidebar. The logo is Streamlit's st.logo; the name and tagline are
    drawn next to it with CSS (a grid: logo | name / tagline)."""
    st.logo(str(ASSETS / "logo-mark.svg"), size="large",
            icon_image=str(ASSETS / "logo-mark.svg"))
    logo = '[data-testid="stSidebarHeader"] > :first-child'
    st.html(
        "<style>"
        # The logo is a plain box on Home and a "go to Home" link on
        # other pages, so target whichever comes first.
        f"{logo} {{ display: grid; grid-template-columns: auto 1fr;"
        "column-gap: .7rem; align-items: center; text-align: left; }"
        f"{logo} img {{ grid-row: 1 / span 2; height: 3rem; width: 3rem;"
        "max-width: none; }"
        f'{logo}::after {{ content: "{_css_text(ministry_name)}";'
        "grid-column: 2; grid-row: 1; align-self: end;"
        'font-family: "Poppins", sans-serif; font-weight: 600;'
        "font-size: 18px; color: #FFFFFF; white-space: nowrap; }"
        f'{logo}::before {{ content: "{_css_text(tagline)}";'
        "grid-column: 2; grid-row: 2; align-self: start;"
        "font-size: 14px; color: #BAC8FF; white-space: nowrap; }"
        "</style>"
    )


def nav_badges(counts):
    """Small coral count pills on menu items, e.g. {"pickups": 3}.
    Only counts above zero are shown. Menu links are found by the end of
    their address (…/pickups), which Streamlit builds from url_path."""
    rules = []
    for path, number in counts.items():
        if number and number > 0:
            rules.append(
                f'[data-testid="stSidebarNavLink"][href$="/{_css_text(path)}"]'
                f'::after {{ content: "{int(number)}"; margin-left: auto;'
                "background: #FF6B6B; color: #1F2A37; border-radius: 999px;"
                "padding: 0 .55rem; font-size: 15px; font-weight: 700;"
                "line-height: 1.6; }"
            )
    if rules:
        st.html("<style>" + "".join(rules) + "</style>")


def profile_html(name, role_words):
    """The signed-in person at the bottom of the sidebar."""
    background, colour = avatar_colours(name)
    return (
        '<div class="fr-profile">'
        f'<div class="fr-avatar" style="background:{background};'
        f'color:{colour}" aria-hidden="true">{html.escape(initials(name))}'
        "</div>"
        f'<div><div class="fr-profile-name">{html.escape(str(name))}</div>'
        f'<span class="fr-profile-role">{html.escape(role_words)}</span>'
        "</div></div>"
    )


@functools.lru_cache(maxsize=None)
def _picture(name):
    """(data URI, description) for an SVG in app/assets."""
    svg = (ASSETS / f"{name}.svg").read_text(encoding="utf-8")
    found = re.search(r'aria-label="([^"]*)"', svg)
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{data}", found.group(1) if found else ""


def illustration(name, width=220):
    """One of the pictures in app/assets (e.g. "welcome", "empty-food").
    Shown as a plain <img> (not st.image), so a decorative picture gets no
    "fullscreen" button. The alt text comes from the SVG's aria-label."""
    source, description = _picture(name)
    st.html(f'<div class="fr-illustration" style="width:{int(width)}px">'
            f'<img src="{source}" alt="{html.escape(description)}"></div>')


def section_title(text, icon=None, tone="blue"):
    """A section title with its icon in a tinted circle and a short coral
    underline. tone: blue, coral, green, purple or teal."""
    with st.container(key=_key(f"section-{tone}")):
        st.subheader(f"{icon} {text}" if icon else text)


def card_title(text, icon, tone="blue"):
    """A card's title with its icon in a tinted circle."""
    with st.container(key=_key(f"ctitle-{tone}")):
        st.markdown(f"#### {icon} {text}")


# Soft avatar colours (background, initials). All pass AA (5.7:1 or more).
AVATAR_COLOURS = [
    ("#DBE4FF", "#2B3FA0"), ("#FFE3E3", "#A51D1D"), ("#D3F9D8", "#1E6B2F"),
    ("#E5DBFF", "#4A2BB0"), ("#C3FAE8", "#0B5D50"), ("#FFEC99", "#7A4A00"),
]


def initials(name):
    words = ["".join(ch for ch in word if ch.isalnum())
             for word in str(name or "").split()]
    letters = "".join(word[0] for word in words if word)[:2].upper()
    return letters or "?"


def avatar_colours(name):
    """The same name always gets the same soft colour."""
    index = zlib.crc32(str(name or "").lower().encode()) % len(AVATAR_COLOURS)
    return AVATAR_COLOURS[index]


def person_html(name, chips=()):
    """Avatar with initials, the name in bold, and small chips (city, type)."""
    background, colour = avatar_colours(name)
    chip_html = "".join(f'<span class="fr-chip">{html.escape(str(c))}</span>'
                        for c in chips if c)
    return (
        '<div class="fr-person">'
        f'<div class="fr-avatar" style="background:{background};'
        f'color:{colour}" aria-hidden="true">{html.escape(initials(name))}'
        "</div>"
        f'<div><div class="fr-name">{html.escape(str(name or ""))}</div>'
        + (f'<div class="fr-chips">{chip_html}</div>' if chip_html else "")
        + "</div></div>"
    )


def person_header(name, chips=()):
    st.html(person_html(name, chips))


PICKUP_STEPS = [("REQUESTED", "Requested"), ("ACCEPTED", "Accepted"),
                ("PICKED_UP", "Picked up"), ("DELIVERED", "Delivered")]


def tracker_html(status):
    """Requested -> Accepted -> Picked up -> Delivered: done steps blue, the
    current step coral. Words are always shown (not colour alone)."""
    codes = [code for code, _ in PICKUP_STEPS]
    if status not in codes:
        return ""
    now_at = codes.index(status)
    finished = status == "DELIVERED"
    items = []
    for number, (code, words) in enumerate(PICKUP_STEPS):
        if finished or number < now_at:
            state, mark = "done", "\u2713"
        elif number == now_at:
            state, mark = "current", str(number + 1)
        else:
            state, mark = "todo", str(number + 1)
        items.append(f'<li class="fr-step {state}"><span class="fr-dot">'
                     f'{mark}</span><span class="fr-label">{words}</span></li>')
    label = ("Delivered: all 4 steps done" if finished else
             f"Step {now_at + 1} of 4: {PICKUP_STEPS[now_at][1]}")
    return (f'<ol class="fr-track" aria-label="{label}">'
            + "".join(items) + "</ol>")


def pickup_tracker(status):
    markup = tracker_html(status)
    if markup:
        st.html(markup)


def _number(value):
    value = float(value or 0)
    return f"{int(value):,}" if value.is_integer() else f"{value:,.1f}"


def impact_html(impact):
    """The Home impact strip: big numbers and one encouraging line."""
    kg = float(impact.get("kg_this_month") or 0)
    donations = int(impact.get("donations_this_month") or 0)
    deliveries = int(impact.get("deliveries") or 0)
    if kg:
        line = f"Together we shared {_number(kg)} kg of food this month."
    elif donations:
        line = (f"Together we shared {plural(donations, 'donation')} "
                "this month.")
    elif deliveries:
        line = "Every delivery so far reached people in need. Thank you!"
    else:
        line = "Your first delivery will appear here."
    stats = [
        (_number(kg), "kg shared this month"),
        (_number(deliveries), "deliveries completed"),
        (_number(impact.get("kitchens")), "partner kitchens"),
        (_number(impact.get("volunteers")), "volunteers"),
    ]
    if all(n == "0" for n, _ in stats):
        # Nothing yet: just the encouraging line, not a row of zeros.
        return (f'<div class="fr-impact"><p class="fr-impact-line">'
                f'{html.escape(line)}</p><p class="fr-num-label">'
                "Every meal shared will be counted here.</p></div>")
    cells = "".join(
        f'<div class="fr-stat"><div class="fr-num">{html.escape(n)}</div>'
        f'<div class="fr-num-label">{html.escape(label)}</div></div>'
        for n, label in stats
    )
    return (f'<div class="fr-impact"><p class="fr-impact-line">'
            f'{html.escape(line)}</p><div class="fr-impact-grid">{cells}'
            "</div></div>")


def impact_strip(impact):
    st.html(impact_html(impact))


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

    tone="royal" / "green" / "teal" / "purple" / "coral" / "red" /
    "amber" gives a white card with a coloured top stripe (stat cards).
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
              button_label=None, page=None, key=None, zero_hint=None):
    """A number card: icon in a coloured circle + big number + label, a
    coloured top stripe, and an optional button to the page where you act.
    When the number is 0, it is shown in a softer grey with `zero_hint`
    (e.g. "Nothing urgent. Great job!") instead of the caption.

    tone: royal, green, teal, purple, coral, red or amber.
    Returns True when its button (not a page link) was clicked.
    """
    with st.container(border=True, key=_key(f"tone-{tone}-stat")):
        st.metric(f"{icon} {label}" if icon else label, value)
        hint = zero_hint if not value and zero_hint else caption
        if hint:
            st.caption(hint)
        return _action(button_label, page=page, key=key)


def stat_row(cards):
    """Stat cards side by side: all in one row on a computer, two per
    row on a phone. `cards` are dicts of stat_card() arguments."""
    with st.container(key=_key("statrow")):
        for column, details in grid(cards, per_row=len(cards)):
            with column:
                stat_card(**details)


def quick_actions(actions):
    """A row of small outlined buttons, e.g. ("Add volunteer",
    ":material/person_add:", page, "volunteer"). A click opens the page
    with that form already open (see form_requested())."""
    with st.container(horizontal=True, key=_key("quick-actions")):
        for label, icon, page, form in actions:
            if st.button(label, icon=icon, key=f"quick_{form}"):
                st.session_state[_FORM_REQUEST] = {
                    "form": form, "page": page.url_path}
                st.switch_page(page)


_FORM_REQUEST = "open_form_request"


def form_requested(form):
    """True if the person came from a quick action for this form, so the
    page shows that form open. It stays True on this page (e.g. after a
    mistake in the form) until they save or go to another page."""
    request = st.session_state.get(_FORM_REQUEST)
    return bool(request) and request["form"] == form


def forget_form_request(current_url_path):
    """Call on every run: a form request only counts on its own page."""
    request = st.session_state.get(_FORM_REQUEST)
    if request and request["page"] != current_url_path:
        st.session_state.pop(_FORM_REQUEST, None)


def progress_html(done, total):
    """A thin progress bar; the words above it say the same thing."""
    percent = int(100 * done / total) if total else 0
    return (f'<div class="fr-progress" role="img" aria-label="{done} of '
            f'{total} done"><div style="width:{percent}%"></div></div>')


def checklist(title, steps):
    """A "Getting started" card. steps: (words, done, page) in order.
    Done steps get a green tick and the word "done"; the next step is
    highlighted. Each step links to the page where it is done."""
    done_count = sum(1 for _, done, _ in steps if done)
    next_step = next((i for i, (_, done, _) in enumerate(steps)
                      if not done), None)
    with card():
        card_title(title, ":material/flag:", "blue")
        st.caption(f"{done_count} of {len(steps)} done. Each step ticks "
                   "itself when it happens.")
        st.html(progress_html(done_count, len(steps)))
        for column, (number, (words, done, page)) in grid(
                list(enumerate(steps))):
            state = ("done" if done else
                     "next" if number == next_step else "todo")
            with column, st.container(key=_key(f"step-{state}")):
                st.page_link(
                    page,
                    label=(f"{number + 1}. {words}"
                           + (" · done" if done else "")),
                    icon=(":material/check_circle:" if done else
                          ":material/arrow_circle_right:"
                          if state == "next" else
                          ":material/radio_button_unchecked:"),
                    width="stretch",
                )


def empty_state(message, icon=":material/inbox:", hint=None,
                button_label=None, page=None, key=None, image=None):
    """Shown instead of an empty list: a picture (or icon), one encouraging
    sentence, and the next step. Returns True when its button (not a link)
    was clicked."""
    with card():
        if image:
            illustration(image, width=180)
        else:
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


# ---------------------------------------------------------------- landing
# The signed-out screens: the sign-in landing page, and the request
# access / waiting / switched-off cards. Their extra CSS is added only
# there (landing_style), so it never touches the signed-in pages.

# Google's "G", drawn in SVG (shown on a white circle on the blue button).
_GOOGLE_G = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85'
    'C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 '
    '13.72 17.74 9.5 24 9.5z"/>'
    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02'
    'h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 '
    '7.09-17.65z"/>'
    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27'
    '-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 '
    '10.78l7.97-6.19z"/>'
    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6'
    'c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 '
    '6.19C6.51 42.62 14.62 48 24 48z"/></svg>'
)
_GOOGLE_G_URI = ("data:image/svg+xml;base64,"
                 + base64.b64encode(_GOOGLE_G.encode()).decode("ascii"))

_LANDING_CSS = """
<style>
/* Signed-out screens: very light background with two soft shapes. */
[data-testid="stApp"] {
    background:
        radial-gradient(circle at 92% 8%, rgba(255, 201, 201, .35) 0,
                        rgba(255, 201, 201, 0) 260px),
        radial-gradient(circle at 4% 70%, rgba(186, 200, 255, .30) 0,
                        rgba(186, 200, 255, 0) 300px),
        linear-gradient(180deg, #F8F9FF 0%, #EEF2FF 100%) fixed;
}
[data-testid="stMainBlockContainer"] { max-width: 1180px; }
/* The page has its own brand row, so hide the small header logo. */
[data-testid="stHeaderLogo"], [data-testid="stHeader"] img { display: none; }

/* Brand row: logo + ministry name. */
.fr-brand-row { display: flex; align-items: center; gap: .7rem; }
.fr-brand-row img { width: 44px; height: 44px; }
.fr-brand-row span {
    font-family: "Poppins", sans-serif; font-weight: 600; font-size: 19px;
    color: #1F2A37;
}

/* Hero: fills most of the first screen on a computer. */
[class*="st-key-landing-hero"] {
    min-height: min(74vh, 760px); justify-content: center;
    padding: 1rem 0 2rem;
}
.fr-hero h1 {
    font-family: "Poppins", sans-serif; font-weight: 700; font-size: 52px;
    line-height: 1.12; color: #1F2A37; margin: 1.6rem 0 1rem; padding: 0;
    letter-spacing: -.01em;
}
.fr-hero h1 em { font-style: normal; color: #364FC7; }
.fr-hero p {
    font-size: 20px; line-height: 1.55; color: #374151; margin: 0;
    max-width: 34rem;
}
.fr-muted { font-size: 15px; color: #4B5563; margin: .2rem 0 0; }

/* The one call to action: big royal-blue pill with Google's G. */
[class*="st-key-google_sign_in"] button {
    min-height: 3.6rem; border-radius: 999px;
    padding: .5rem 1.8rem .5rem .55rem; margin-top: 1.4rem;
    box-shadow: 0 10px 24px rgba(54, 79, 199, .30);
}
[class*="st-key-google_sign_in"] button p { font-size: 19px; }
[class*="st-key-google_sign_in"] button::before {
    content: ""; flex: 0 0 auto; width: 2.5rem; height: 2.5rem;
    margin-right: .8rem; border-radius: 50%;
    background: #FFFFFF url("GOOGLE_G") center / 1.45rem no-repeat;
}

/* Picture on a soft blurred lavender -> light coral blob, floating. */
.fr-hero-art { position: relative; max-width: 500px; margin: 0 auto; }
.fr-hero-art::before {
    content: ""; position: absolute; inset: 4% 2%;
    border-radius: 46% 54% 52% 48% / 55% 45% 55% 45%;
    background: linear-gradient(135deg, #E5DBFF 0%, #FFD8D8 100%);
    filter: blur(26px);
}
.fr-hero-art img {
    position: relative; display: block; width: 100%; height: auto;
    filter: drop-shadow(0 22px 28px rgba(54, 79, 199, .18));
    animation: fr-float 6s ease-in-out infinite;
}
@keyframes fr-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
@media (prefers-reduced-motion: reduce) {
    .fr-hero-art img { animation: none; }
}

/* Section headings and the small step / role cards. */
.fr-landing-h2 {
    font-family: "Poppins", sans-serif; font-weight: 700; font-size: 30px;
    color: #1F2A37; text-align: center; margin: 2.2rem 0 .4rem; padding: 0;
}
[class*="st-key-card-how"], [class*="st-key-card-join"] {
    padding: 1.3rem 1.3rem 1rem;
}
[class*="st-key-card-how"] [data-testid="stCaptionContainer"] p {
    font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
    color: #364FC7;
}

/* Slim footer. */
.fr-footer {
    display: flex; flex-wrap: wrap; justify-content: center; gap: .4rem 1.4rem;
    border-top: 1px solid #DBE4FF; margin-top: 2.5rem; padding: 1.2rem 0 .5rem;
    font-size: 15px; color: #4B5563;
}
.fr-footer a { color: #2B3FA0; display: inline-block; padding: 10px 0; }
.fr-footer strong { color: #1F2A37; }

/* The second sign-in button at the bottom is for phones only. */
[class*="st-key-phone-only"] { display: none; }

@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }
    [class*="st-key-landing-hero"] { min-height: 0; padding: 0; }
    .fr-hero h1 { font-size: 34px; margin: 1.1rem 0 .7rem; }
    .fr-hero p { font-size: 18px; }
    [class*="st-key-google_sign_in"],
    [class*="st-key-google_sign_in"] .stButton,
    [class*="st-key-google_sign_in"] button { width: 100%; }
    [class*="st-key-google_sign_in"] button { margin-top: 1rem; }
    .fr-hero-art { max-width: 250px; margin-top: .5rem; }
    .fr-landing-h2 { font-size: 26px; margin-top: 1.4rem; }
    [class*="st-key-phone-only"] { display: block; }
}
</style>
""".replace("GOOGLE_G", _GOOGLE_G_URI)


def landing_style():
    """Extra look for the signed-out screens (call once per run there)."""
    st.html(_LANDING_CSS)


def brand_row_html(ministry_name):
    source, _ = _picture("logo-mark")
    return (f'<div class="fr-brand-row"><img src="{source}" alt="">'
            f"<span>{html.escape(ministry_name)}</span></div>")


def hero_text_html(ministry_name, headline, subline, highlight=None):
    """Brand row, the big headline (a real <h1>) and one short line.
    `highlight`: words of the headline shown in royal blue."""
    title = html.escape(headline)
    if highlight:
        title = title.replace(html.escape(highlight),
                              f"<em>{html.escape(highlight)}</em>", 1)
    return (f'<div class="fr-hero">{brand_row_html(ministry_name)}'
            f"<h1>{title}</h1>"
            f"<p>{html.escape(subline)}</p></div>")


def hero_picture_html(name):
    source, description = _picture(name)
    return (f'<div class="fr-hero-art"><img src="{source}" '
            f'alt="{html.escape(description)}"></div>')


def info_cards(cards, kind):
    """Three small white cards side by side (stacked on a phone).
    cards: (step words or None, title, icon, tone, line)."""
    for column, (step, title, icon, tone, line) in grid(cards,
                                                         per_row=len(cards)):
        with column, st.container(border=True, key=_key(f"card-{kind}")):
            if step:
                st.caption(step)
            card_title(title, icon, tone)
            st.markdown(line)


def footer_html(ministry_name, privacy_link, contact_email):
    email = html.escape(contact_email)
    return (
        '<footer class="fr-footer">'
        f"<strong>{html.escape(ministry_name)}</strong>"
        f'<a href="{html.escape(privacy_link)}" target="_self">'
        "Privacy policy</a>"
        f'<a href="mailto:{email}">{email}</a>'
        "<span>Run by volunteers</span></footer>"
    )


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


# ---------------------------------------------------------------- messages

def flash_success(message, toast=None, celebrate=False):
    """Show a green success message after the page refreshes with fresh
    data. Say what happened AND what happens next. `toast` adds a small
    pop-up; `celebrate` adds balloons (use rarely, e.g. a first delivery)."""
    from app.backend import clear_caches

    clear_caches()  # safety net: every write also clears in app/backend.py
    st.session_state.pop(_FORM_REQUEST, None)  # saved: close the form
    st.session_state["flash"] = {"message": message, "toast": toast,
                                 "celebrate": celebrate}
    st.rerun()


def show_flash():
    """Show the message saved by flash_success(), once."""
    if "flash" not in st.session_state:
        return
    flash = st.session_state.pop("flash")
    if isinstance(flash, str):
        flash = {"message": flash}
    st.success(flash["message"], icon=":material/check_circle:")
    if flash.get("toast"):
        st.toast(flash["toast"], icon=":material/celebration:")
    if flash.get("celebrate"):
        st.balloons()


def rows(response, key):
    """The list inside a backend response, or [] after showing its error."""
    if "error" in response:
        st.error(response["error"], icon=":material/error:")
        return []
    return response.get(key, [])


def amount(quantity, unit):
    """'20 kg', '15.5 kg', '100 pieces'."""
    quantity = float(quantity)
    shown = int(quantity) if quantity.is_integer() else quantity
    return f"{shown} {unit or ''}".strip()


def plural(number, word, many=None):
    """'1 pickup', '3 pickups', '2 people' (with many='people')."""
    if number == 1:
        return f"1 {word}"
    return f"{number} {many or word + 's'}"


# ---------------------------------------------------------------- charts
# Same colours as the badges (see .streamlit/config.toml).
COLOUR_HEX = {
    "green": "#2B8A3E", "yellow": "#F59F00", "blue": "#0CA678",
    "violet": "#7048E8", "red": "#E03131", "gray": "#868E96",
    "primary": "#364FC7", "orange": "#F03E3E",
}


def status_chart(title, counts):
    """Horizontal bar chart of statuses, coloured like the badges, with the
    number written on each bar (so colour is never the only clue).

    counts: list of (status code, number), in the order to show.
    """
    import altair as alt

    data = [
        {"Status": status_style(code)[0], "Count": int(number or 0),
         "Colour": COLOUR_HEX.get(status_style(code)[1], "#868E96")}
        for code, number in counts
    ]
    order = [row["Status"] for row in data]
    # Leave room after the longest bar for its number.
    biggest = max([row["Count"] for row in data] + [1])
    base = alt.Chart(alt.Data(values=data)).encode(
        y=alt.Y("Status:N", sort=order, title=None,
                axis=alt.Axis(labelFontSize=15, labelLimit=200,
                              labelColor="#1F2A37")),
        x=alt.X("Count:Q", title=None, axis=None,
                scale=alt.Scale(domain=[0, biggest * 1.2])),
    )
    bars = base.mark_bar(cornerRadiusEnd=6, height=26).encode(
        color=alt.Color("Colour:N", scale=None, legend=None),
        tooltip=["Status:N", "Count:Q"],
    )
    labels = base.mark_text(align="left", dx=6, fontSize=15,
                            fontWeight="bold", color="#1F2A37").encode(
        text="Count:Q",
    )
    with card():
        st.markdown(f"**{title}**")
        st.altair_chart((bars + labels).properties(height=44 * len(data)),
                        width="stretch")
