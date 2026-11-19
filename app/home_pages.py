"""Home page for each role: answers "what do I need to do now?".

    Admin         today's numbers as cards, urgent food first
    Donor         big "Share surplus food" button + my recent donations
    Organization  food it can request right now + its own requests
    Volunteer     today's pickups in order, with big Picked up / Delivered

All data comes from app/backend.py, which returns {"error": ...} instead
of raising, so a database hiccup shows a message, not a crash.
"""

from datetime import timedelta

import streamlit as st

from app import ui
from app.backend import (
    create_pickup_from_api,
    get_available_donations_from_api,
    get_food_risk_analysis_from_api,
    get_my_donations_from_api,
    get_pending_organizations_from_api,
    get_pickup_requests_from_api,
    get_pickup_summary_from_api,
    get_requestable_donations_from_api,
    get_volunteer_pickups_from_api,
    update_pickup_status_from_api,
)
from app.timeutil import now_local
from app.user_service import list_users

ACTIVE_FOR_VOLUNTEER = ("ACCEPTED", "PICKED_UP")


# ---------------------------------------------------------------- helpers

def _rows(response, key):
    """The list inside a backend response, or [] after showing the error."""
    if "error" in response:
        st.error(response["error"], icon=":material/error:")
        return []
    return response.get(key, [])


def _greeting(now):
    if now.hour < 12:
        return "Good morning"
    if now.hour < 17:
        return "Good afternoon"
    return "Good evening"


def _first_name(user):
    name = (user.get("full_name") or "").strip()
    return name.split(" ")[0] if name else "friend"


def _amount(quantity, unit):
    quantity = float(quantity)
    shown = int(quantity) if quantity.is_integer() else quantity
    return f"{shown} {unit or ''}".strip()


def _plural(count, word):
    return f"{count} {word}" + ("" if count == 1 else "s")


# ---------------------------------------------------------------- entry

def show_home(user, my_restaurant, my_organization, pages, flash_success):
    """Draw the right home page. `pages` maps url path -> st.Page."""
    now = now_local()
    role = user["role"]
    if role == "ADMIN":
        _admin_home(user, pages, now)
    elif role == "DONOR":
        _donor_home(user, my_restaurant, pages, now)
    elif role == "ORGANIZATION":
        _organization_home(user, my_organization, pages, now, flash_success)
    elif role == "VOLUNTEER":
        _volunteer_home(user, pages, now, flash_success)


# ---------------------------------------------------------------- admin

def _admin_home(user, pages, now):
    available = _rows(get_available_donations_from_api(), "donations")
    risks = _rows(get_food_risk_analysis_from_api(), "risk_analysis")
    urgent = sorted(
        (r for r in risks if r["risk_level"] == "HIGH"),
        key=lambda r: r["hours_remaining"],
    )
    expired_uncollected = [
        r for r in risks
        if r["risk_level"] == "EXPIRED" and r["donation_status"] == "AVAILABLE"
    ]
    summary = get_pickup_summary_from_api()
    waiting_pickups = 0 if "error" in summary else summary["requested_pickups"]
    people = list_users(status="PENDING")
    orgs = _rows(get_pending_organizations_from_api(), "organizations")

    todo = []
    if urgent:
        todo.append(_plural(len(urgent), "urgent item"))
    if waiting_pickups:
        todo.append(_plural(waiting_pickups, "pickup") + " to accept")
    if people:
        todo.append(("1 person" if len(people) == 1
                     else f"{len(people)} people") + " to approve")
    if orgs:
        todo.append(_plural(len(orgs), "organization") + " to verify")
    purpose = (
        "Needs you today: " + ", ".join(todo) + "."
        if todo else "All caught up. Nothing needs you right now."
    )
    ui.page_header(f"{_greeting(now)}, {_first_name(user)}!", purpose,
                   icon=":material/wb_sunny:")

    # Urgent food first: it is the one thing that cannot wait.
    if urgent:
        with ui.card("coral"):
            st.subheader(":orange[:material/priority_high:] Expiring in under "
                         "2 hours")
            for item in urgent:
                st.markdown(
                    f"**{item['food_name']}** · "
                    f"{_amount(item['quantity'], item['unit'])} · expires "
                    f"**{ui.friendly_time(item['expiry_time'], now)}**  \n"
                    f"{ui.badge_markdown(item['donation_status'])}"
                )
            st.page_link(pages["pickups"], label="Arrange pickups",
                         icon=":material/arrow_forward:", width="stretch")

    cards = [
        dict(label="Food available", value=len(available),
             caption="donations ready to request",
             icon=":material/restaurant:", tone="green",
             button_label="See food", page=pages["donations"]),
        dict(label="Urgent", value=len(urgent),
             caption="expires in under 2 hours",
             icon=":material/priority_high:", tone="coral",
             button_label="See pickups", page=pages["pickups"]),
        dict(label="Pickups to accept", value=waiting_pickups,
             caption="requested by organizations",
             icon=":material/hourglass_top:", tone="royal",
             button_label="Accept and assign volunteers",
             page=pages["pickups"]),
        dict(label="People to approve", value=len(people),
             caption="asked to join", icon=":material/person_add:",
             tone="purple", button_label="Review requests",
             page=pages["user-access"]),
    ]
    for column, details in ui.grid(cards):
        with column:
            ui.stat_card(**details)

    if orgs:
        with ui.card("teal"):
            st.markdown(
                f":material/verified: **{_plural(len(orgs), 'organization')}"
                "** waiting to be verified."
            )
            st.page_link(pages["admin"], label="Verify organizations",
                         icon=":material/arrow_forward:", width="stretch")
    if expired_uncollected:
        st.caption(
            f"{_plural(len(expired_uncollected), 'donation')} expired "
            "without being collected."
        )


# ---------------------------------------------------------------- donor

def _donor_home(user, my_restaurant, pages, now):
    ui.page_header(
        f"{_greeting(now)}, {_first_name(user)}!",
        "Have food to spare? Share it in a minute, and a nearby home or "
        "shelter can request it.",
        icon=":material/wb_sunny:",
    )

    if not my_restaurant:
        ui.empty_state(
            "First, tell us about your kitchen",
            icon=":material/storefront:",
            hint="Add your restaurant or kitchen once. Then you can share "
                 "food any time.",
            button_label="Add my kitchen", page=pages["my-restaurant"],
        )
        return

    if st.button("Share surplus food", type="primary",
                 icon=":material/add_circle:", width="stretch"):
        st.switch_page(pages["donations"])

    st.subheader("My recent donations")
    donations = _rows(get_my_donations_from_api(my_restaurant[0]),
                      "donations")
    if not donations:
        ui.empty_state(
            "You haven't shared any food yet",
            icon=":material/soup_kitchen:",
            hint="When you share food, you'll see here when it is "
                 "requested, picked up and delivered.",
        )
        return

    for (_, food_name, quantity, unit, expiry_time, status,
         _created) in donations:
        expired = (status == "AVAILABLE"
                   and ui.to_datetime(expiry_time) <= now)
        shown_status = "EXPIRED" if expired else status
        when = ("expired" if expired else
                f"expires {ui.friendly_time(expiry_time, now)}"
                if status in ("AVAILABLE", "RESERVED") else
                f"best before {ui.clock_time(expiry_time)}")
        with ui.card():
            st.markdown(
                f"**{food_name}** · {_amount(quantity, unit)}  \n"
                f"{ui.badge_markdown(shown_status)} · {when}"
            )


# ---------------------------------------------------------------- organization

def _organization_home(user, organization, pages, now, flash_success):
    ui.page_header(
        f"{_greeting(now)}, {_first_name(user)}!",
        "Find good food for the people you serve, and follow your "
        "requests.",
        icon=":material/wb_sunny:",
    )

    if not organization:
        ui.empty_state(
            "First, tell us about your organization",
            icon=":material/apartment:",
            hint="A coordinator checks every organization before it can "
                 "request food.",
            button_label="Add my organization",
            page=pages["my-organization"],
        )
        return

    (organization_id, organization_name, *_rest) = organization
    city = organization[6]
    verification = organization[8]
    if verification != "VERIFIED":
        with ui.card():
            st.markdown(f"**{organization_name}**  \n"
                        f"{ui.badge_markdown(verification)}")
            st.markdown(
                "A coordinator will check your organization. Once it is "
                "verified you can request food here."
                if verification == "PENDING" else
                "Your organization was not approved. Please contact the "
                "ministry admin."
            )
        return

    food = _rows(get_requestable_donations_from_api(), "donations")
    # Food in the organization's own city first, then soonest expiry.
    same_city = (city or "").strip().lower()
    food.sort(key=lambda d: ((d[12] or "").strip().lower() != same_city,
                             d[7]))

    st.subheader("Available food near you" if same_city
                 else "Available food")
    if not food:
        ui.empty_state(
            "No food is waiting right now",
            icon=":material/restaurant:",
            hint="New donations appear here as soon as they are shared. "
                 "Please check again later.",
        )
    for donation in food:
        _food_card(donation, organization_id, now, flash_success)
    if st.session_state.get(_CHOSEN_FOOD):
        _request_dialog(*st.session_state[_CHOSEN_FOOD], organization_id,
                        flash_success)

    st.subheader("My requests")
    requests = _rows(
        get_pickup_requests_from_api(organization_id=organization_id),
        "pickups",
    )
    if not requests:
        st.caption("You haven't requested any food yet.")
    for pickup in requests[:5]:
        _pickup_line(pickup, now, show_organization=False)
    if len(requests) > 5:
        st.page_link(pages["pickups"], label="See all my requests",
                     icon=":material/arrow_forward:")


def _food_card(donation, organization_id, now, flash_success):
    (donation_id, restaurant, food_name, _category, quantity, unit,
     _prepared, expiry_time, food_type, _packaging, pickup_address,
     _status, city) = donation
    food_type_words = (food_type or "").replace("_", " ").capitalize()
    with ui.card():
        st.markdown(
            f"**{food_name}** · {_amount(quantity, unit)}"
            + (f" · {food_type_words}" if food_type_words else "")
        )
        st.markdown(
            f":material/storefront: {restaurant}"
            + (f", {city}" if city else "") + "  \n"
            + (f":material/location_on: {pickup_address}  \n"
               if pickup_address else "")
            + f":material/schedule: Expires "
            f"**{ui.friendly_time(expiry_time, now)}**"
        )
        if st.button("Request this food", key=f"request_{donation_id}",
                     type="primary", icon=":material/volunteer_activism:",
                     width="stretch"):
            st.session_state[_CHOSEN_FOOD] = [
                donation_id, food_name, expiry_time, pickup_address,
            ]


# "When can you collect it?" choices, so nobody fights a date picker.
_COLLECT_CHOICES = (
    ("As soon as possible (about 30 min)", 30),
    ("In about 1 hour", 60),
    ("In about 2 hours", 120),
    ("In about 4 hours", 240),
)


_CHOSEN_FOOD = "request_food_chosen"


def _forget_chosen_food():
    st.session_state.pop(_CHOSEN_FOOD, None)


@st.dialog("Request this food", on_dismiss=_forget_chosen_food)
def _request_dialog(donation_id, food_name, expiry_time, pickup_address,
                    organization_id, flash_success):
    now = now_local()
    expiry = ui.to_datetime(expiry_time)
    choices = [label for label, minutes in _COLLECT_CHOICES
               if now + timedelta(minutes=minutes) < expiry]
    st.markdown(f"**{food_name}** expires "
                f"**{ui.friendly_time(expiry_time, now)}**.")
    if not choices:
        st.warning("This food expires too soon to be collected safely.")
        _forget_chosen_food()
        return
    when = st.radio("When can a volunteer collect it?", choices)
    notes = st.text_area(
        "Anything the coordinator should know? (optional)",
        placeholder="e.g. we need it for 40 people tonight",
    )
    if st.button("Send request", type="primary", icon=":material/send:",
                 width="stretch"):
        minutes = dict(_COLLECT_CHOICES)[when]
        result = create_pickup_from_api({
            "donation_id": donation_id,
            "organization_id": organization_id,
            "pickup_time": (now_local()
                            + timedelta(minutes=minutes)).isoformat(),
            "pickup_address": pickup_address,
            "notes": notes.strip() or None,
        })
        if "error" in result:
            st.error(result["error"])
        else:
            _forget_chosen_food()
            flash_success(
                f"Request sent for {food_name}. Next: a coordinator "
                "accepts it and assigns a volunteer. You can follow it "
                "under My requests."
            )


def _pickup_line(pickup, now, show_organization=True):
    (_, food_name, quantity, unit, restaurant, organization, _requested,
     pickup_time, status, _address, _notes, _volunteer_id,
     volunteer_name) = pickup[:13]
    with ui.card():
        details = [f"from {restaurant}"]
        if show_organization:
            details.append(f"to {organization}")
        if pickup_time and status not in ("DELIVERED",):
            details.append(f"pickup {ui.friendly_time(pickup_time, now)}")
        if volunteer_name and status in ("ACCEPTED", "PICKED_UP"):
            details.append(f"volunteer: {volunteer_name}")
        st.markdown(
            f"**{food_name}** · {_amount(quantity, unit)}  \n"
            f"{ui.badge_markdown(status)} · " + " · ".join(details)
        )


# ---------------------------------------------------------------- volunteer

def _volunteer_home(user, pages, now, flash_success):
    if not user.get("volunteer_id"):
        ui.page_header(f"{_greeting(now)}, {_first_name(user)}!",
                       "Your volunteer profile is not set up yet.",
                       icon=":material/wb_sunny:")
        st.info("Please ask the ministry admin to finish setting up your "
                "volunteer profile.", icon=":material/info:")
        return

    # Includes the delivery address and contact, but only for this
    # volunteer's active pickups (enforced in the query).
    pickups = _rows(get_volunteer_pickups_from_api(user["volunteer_id"]),
                    "pickups")
    active = sorted(
        (p for p in pickups if p[8] in ACTIVE_FOR_VOLUNTEER),
        key=lambda p: ui.to_datetime(p[7]) or now,
    )
    today = [p for p in active
             if (ui.to_datetime(p[7]) or now).date() <= now.date()]
    later = [p for p in active if p not in today]

    ui.page_header(
        f"{_greeting(now)}, {_first_name(user)}!",
        f"You have {_plural(len(today), 'pickup')} today. Thank you!"
        if today else
        "No pickups for you today. We'll assign you one when food is ready.",
        icon=":material/wb_sunny:",
    )

    st.subheader("My pickups today")
    if not today:
        ui.empty_state("Nothing to collect right now",
                       icon=":material/directions_walk:")
    for number, pickup in enumerate(today, start=1):
        _volunteer_card(number, pickup, now, flash_success)

    if later:
        st.subheader("Coming up")
        for pickup in later:
            _pickup_line(pickup, now)


def _volunteer_card(number, pickup, now, flash_success):
    (pickup_id, food_name, quantity, unit, restaurant, organization,
     _requested, pickup_time, status, address, notes, _volunteer_id,
     _name, delivery_address, delivery_contact, delivery_phone) = pickup
    when = ui.to_datetime(pickup_time)
    with ui.card():
        st.markdown(
            f"### {number}. {ui.clock_time(when).split(', ')[-1]}"
            f" · {ui.friendly_time(when, now)}"
        )
        st.markdown(ui.badge_markdown(status))
        st.markdown(
            f":material/restaurant: **{food_name}** · "
            f"{_amount(quantity, unit)}  \n"
            f":material/storefront: Collect from **{restaurant}**"
            + (f"  \n:material/location_on: {address}" if address else "")
            + f"  \n:material/home: Deliver to **{organization}**"
            + (f"  \n:material/location_on: {delivery_address}"
               if delivery_address else "")
            + (f"  \n:material/call: {delivery_contact or 'Call'}: "
               f"[{delivery_phone}](tel:{delivery_phone})"
               if delivery_phone else "")
            + (f"  \n:material/sticky_note_2: {notes}" if notes else "")
        )
        if status == "ACCEPTED":
            label, new_status, done = (
                "Picked up", "PICKED_UP",
                f"Marked {food_name} as picked up. Next: deliver it to "
                f"{organization}.",
            )
        else:
            label, new_status, done = (
                "Delivered", "DELIVERED",
                f"Marked {food_name} as delivered. Thank you for serving!",
            )
        if st.button(label, key=f"progress_{pickup_id}", type="primary",
                     icon=":material/check_circle:", width="stretch"):
            result = update_pickup_status_from_api(pickup_id, new_status)
            if "error" in result:
                st.error(result["error"])
            else:
                flash_success(done)
