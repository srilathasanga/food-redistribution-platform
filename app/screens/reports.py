"""Reports & tools (admin): how the ministry is doing, and food that
needs attention."""

import streamlit as st

from app import ui
from app.backend import (
    get_donation_summary_from_api,
    get_food_risk_analysis_from_api,
    get_organization_summary_from_api,
    get_pickup_summary_from_api,
    get_volunteer_summary_from_api,
)
from app.timeutil import now_local

# Most urgent first.
URGENCY_ORDER = {"HIGH": 0, "MEDIUM": 1, "EXPIRED": 2, "LOW": 3}


def _summary(response):
    """A summary dict, or None after showing the error."""
    if "error" in response:
        st.error(response["error"], icon=":material/error:")
        return None
    return response


def reports_page(ctx):
    now = now_local()
    ui.page_header("Reports & tools",
                   "How the ministry is doing, and food that needs "
                   "attention.",
                   icon=":material/insights:")

    donations = _summary(get_donation_summary_from_api())
    pickups = _summary(get_pickup_summary_from_api())
    volunteers = _summary(get_volunteer_summary_from_api())
    organizations = _summary(get_organization_summary_from_api())

    # ---- Impact in numbers
    cards = []
    if donations:
        cards += [
            dict(label="Food shared", value=donations["total_donations"],
                 caption="donations so far", icon=":material/soup_kitchen:",
                 tone="royal"),
            dict(label="Delivered", value=donations["delivered_donations"],
                 caption="reached people in need",
                 icon=":material/task_alt:", tone="green"),
        ]
    if volunteers:
        cards.append(dict(
            label="Volunteers", value=volunteers["active_volunteers"],
            caption=f"{volunteers['available_volunteers']} free right now",
            icon=":material/directions_walk:", tone="teal",
            button_label="See volunteers", page=ctx.pages["volunteers"]))
    if organizations:
        cards.append(dict(
            label="Organizations",
            value=organizations["verified_organizations"],
            caption=(f"verified · {organizations['pending_organizations']} "
                     "waiting"),
            icon=":material/groups:", tone="purple",
            button_label="See organizations",
            page=ctx.pages["organizations"]))
    for column, details in ui.grid(cards):
        with column:
            ui.stat_card(**details)

    # ---- Where things stand (charts use the badge colours)
    charts = []
    if donations:
        charts.append(("Donations by status", [
            ("AVAILABLE", donations["available_donations"]),
            ("RESERVED", donations["reserved_donations"]),
            ("PICKED_UP", donations["picked_up_donations"]),
            ("DELIVERED", donations["delivered_donations"]),
        ]))
    if pickups:
        charts.append(("Pickups by status", [
            ("REQUESTED", pickups["requested_pickups"]),
            ("ACCEPTED", pickups["accepted_pickups"]),
            ("PICKED_UP", pickups["picked_up_pickups"]),
            ("DELIVERED", pickups["delivered_pickups"]),
        ]))
    if charts:
        ui.section_title("Where things stand", ":material/bar_chart:",
                         "blue")
        for column, (title, counts) in ui.grid(charts):
            with column:
                ui.status_chart(title, counts)

    _food_needing_attention(ctx, now)


def _food_needing_attention(ctx, now):
    ui.section_title("Food that needs attention",
                     ":material/priority_high:", "coral")
    risks = ui.rows(get_food_risk_analysis_from_api(), "risk_analysis")
    if not risks:
        st.success("No food is waiting to be collected right now.",
                   icon=":material/task_alt:")
        return

    counts = {level: sum(1 for r in risks if r["risk_level"] == level)
              for level in URGENCY_ORDER}
    st.markdown(" ".join(
        f"{ui.badge_markdown(level)} **{counts[level]}**"
        for level in ("HIGH", "MEDIUM", "LOW", "EXPIRED") if counts[level]
    ))

    risks.sort(key=lambda r: (URGENCY_ORDER.get(r["risk_level"], 9),
                              r["hours_remaining"]))
    needs_attention = [r for r in risks if r["risk_level"] != "LOW"]
    plenty_of_time = [r for r in risks if r["risk_level"] == "LOW"]

    if not needs_attention:
        st.caption("Nothing urgent. All food has plenty of time.")
    for column, risk in ui.grid(needs_attention):
        with column:
            _risk_card(risk, now)
    if needs_attention:
        st.page_link(ctx.pages["pickups"], label="Arrange pickups",
                     icon=":material/arrow_forward:")
    if plenty_of_time:
        with st.expander(f"Plenty of time ({len(plenty_of_time)})",
                         icon=":material/check_circle:"):
            for column, risk in ui.grid(plenty_of_time):
                with column:
                    _risk_card(risk, now)


def _risk_card(risk, now):
    expired = risk["risk_level"] == "EXPIRED"
    with ui.card():
        st.markdown(f"**{risk['food_name']}** · "
                    f"{ui.amount(risk['quantity'], risk['unit'])}")
        st.markdown(ui.badge_markdown(risk["risk_level"]) + " "
                    + ui.badge_markdown(risk["donation_status"]))
        st.markdown(
            (":material/error: Expired "
             if expired else ":material/schedule: Expires ")
            + f"**{ui.friendly_time(risk['expiry_time'], now)}**  \n"
            f":material/lightbulb: {risk['recommended_action']}"
        )
