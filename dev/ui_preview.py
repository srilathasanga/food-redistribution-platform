"""Design preview: every building block from app/ui.py on one page.

Uses made-up sample data only. No login, no database.
Run from the project folder (so the theme in .streamlit/config.toml loads):

    streamlit run dev/ui_preview.py
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import ui  # noqa: E402
from app.timeutil import now_local  # noqa: E402

st.set_page_config(page_title="Design preview", page_icon="🍲",
                   layout="centered")
ui.apply_style()
now = now_local()

st.info("Design preview with sample data. Nothing here is real or saved.",
        icon=":material/palette:")

# ------------------------------------------------------------ page header
ui.page_header(
    "Good morning, Grace",
    "3 pickups are waiting for a volunteer and 1 item expires soon.",
    icon=":material/soup_kitchen:",
)

# ------------------------------------------------------------ stat cards
st.subheader("Stat cards")
col1, col2 = st.columns(2)
with col1:
    ui.stat_card("Food available", 12, caption="donations ready to request",
                 icon=":material/restaurant:", button_label="See food",
                 key="s1")
    ui.stat_card("Pickups waiting", 3, caption="need a volunteer",
                 icon=":material/hourglass_top:",
                 button_label="Assign volunteers", key="s3")
with col2:
    ui.stat_card("Urgent", 1, caption="expires in under 2 hours",
                 icon=":red[:material/priority_high:]",
                 button_label="See urgent food", key="s2")
    ui.stat_card("People to approve", 2, caption="asked to join",
                 icon=":material/person_add:", button_label="Review requests",
                 key="s4")

# ------------------------------------------------------------ badges
st.subheader("Status badges")
st.caption("Each badge has words and an icon, so it never relies on colour.")
st.markdown(" ".join(ui.badge_markdown(code) for code in (
    "AVAILABLE", "RESERVED", "PICKED_UP", "DELIVERED", "EXPIRED")))
st.markdown(" ".join(ui.badge_markdown(code) for code in (
    "REQUESTED", "ACCEPTED", "PENDING", "VERIFIED", "REJECTED")))
st.markdown(" ".join(ui.badge_markdown(code) for code in (
    "HIGH", "MEDIUM", "LOW", "BUSY", "DISABLED")))

# ------------------------------------------------------------ section card
st.subheader("Section card (how a food item will look)")
with ui.section_card():
    top, badge = st.columns([3, 2], vertical_alignment="center")
    top.markdown("**Vegetable biryani** · 20 kg")
    with badge:
        ui.status_badge("AVAILABLE")
    st.markdown(
        f":material/storefront: Green Leaf Restaurant  \n"
        f":material/location_on: 123 Main Road, Ameerpet  \n"
        f":material/schedule: Expires "
        f"**{ui.friendly_time(now + timedelta(minutes=95))}** "
        f"({ui.clock_time(now + timedelta(minutes=95))})"
    )
    st.button("Request this food", type="primary", width="stretch",
              key="req")

with ui.section_card("Today's pickups", "In the order to collect them."):
    st.markdown(f"1. Hope Shelter · {ui.badge_markdown('ACCEPTED')}")
    st.markdown(f"2. Grace Home · {ui.badge_markdown('PICKED_UP')}")

# ------------------------------------------------------------ empty state
st.subheader("Empty state")
ui.empty_state(
    "You haven't shared any food yet",
    icon=":material/soup_kitchen:",
    hint="When you have surplus food, share it here and a nearby "
         "organization can request it.",
    button_label="Share surplus food", key="empty",
)

# ------------------------------------------------------------ times
st.subheader("Friendly times (India time)")
for delta in (timedelta(minutes=45), timedelta(hours=-2), timedelta(0),
              timedelta(hours=30)):
    st.write(f"- {ui.friendly_time(now + delta)}")

# ------------------------------------------------------------ chart
st.subheader("Chart colours")
st.bar_chart(
    pd.DataFrame({"Donations": [12, 4, 7, 30]},
                 index=["Available", "Reserved", "Picked up", "Delivered"]),
    color="#1E6B4E", horizontal=True,
)

# ------------------------------------------------------------ form
st.subheader("Form")
with st.form("preview_form"):
    st.text_input("What food is it?", placeholder="e.g. Vegetable biryani",
                  help="A short name volunteers will recognise.")
    st.form_submit_button("Share surplus food", type="primary",
                          width="stretch")
