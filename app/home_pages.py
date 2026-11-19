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
    get_admin_home_counts_from_api,
    get_impact_from_api,
    get_my_donations_from_api,
    get_pickup_requests_from_api,
    get_requestable_donations_from_api,
    get_urgent_food_from_api,
    get_volunteer_pickups_from_api,
    update_pickup_status_from_api,
)
from app.timeutil import now_local

ACTIVE_FOR_VOLUNTEER = ("ACCEPTED", "PICKED_UP")


# ---------------------------------------------------------------- helpers

def _greeting(now):
    if now.hour < 12:
        return "Good morning"
    if now.hour < 17:
        return "Good afternoon"
    return "Good evening"


def greeting_icon(now):
    """Sun before 5 pm, moon in the evening (India time)."""
    return ":material/wb_sunny:" if now.hour < 17 else ":material/bedtime:"


def _first_name(user):
    name = (user.get("full_name") or "").strip()
    return name.split(" ")[0] if name else "friend"


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


def _impact(now):
    """The ministry's numbers (cached), or None if they cannot load."""
    month_start = now.replace(day=1, hour=0, minute=0, second=0,
                              microsecond=0)
    impact = get_impact_from_api(month_start.isoformat())
    return None if "error" in impact else impact


def _impact_strip(now, impact=None):
    """The ministry's impact so far (totals for everyone, not per person),
    shown only once the first delivery is done: before that it would be
    a strip of zeros. Nothing is shown if the numbers cannot be loaded."""
    impact = impact or _impact(now)
    if impact and impact.get("deliveries"):
        ui.impact_strip(impact)


def getting_started_steps(impact, pages):
    """The admin's first four steps, ticked from real data:
    (words, done, page)."""
    return [
        ("Add your first restaurant", bool(impact.get("kitchens")),
         pages["restaurants"]),
        ("Verify an organization", bool(impact.get("organizations")),
         pages["organizations"]),
        ("Approve a volunteer", bool(impact.get("volunteers")),
         pages["user-access"]),
        ("Complete your first delivery", bool(impact.get("deliveries")),
         pages["pickups"]),
    ]


# ---------------------------------------------------------------- admin

def _admin_home(user, pages, now):
    # All of today's numbers in ONE database query (see dashboard_service).
    counts = get_admin_home_counts_from_api()
    if "error" in counts:
        st.error(counts["error"], icon=":material/error:")
        counts = {}
    urgent_count = counts.get("urgent", 0)
    waiting_pickups = counts.get("pickups_to_accept", 0)
    people_count = counts.get("people_to_approve", 0)
    orgs_count = counts.get("organizations_to_verify", 0)
    expired_count = counts.get("expired_uncollected", 0)
    # The urgent list itself is only fetched when something is urgent.
    urgent = (ui.rows(get_urgent_food_from_api(), "donations")
              if urgent_count else [])

    todo = []
    if urgent_count:
        todo.append(ui.plural(urgent_count, "urgent item"))
    if waiting_pickups:
        todo.append(ui.plural(waiting_pickups, "pickup") + " to accept")
    if people_count:
        todo.append(ui.plural(people_count, "person", "people")
                    + " to approve")
    if orgs_count:
        todo.append(ui.plural(orgs_count, "organization") + " to verify")
    purpose = (
        "Needs you today: " + ", ".join(todo) + "."
        if todo else "All caught up. Nothing needs you right now."
    )
    ui.page_header(f"{_greeting(now)}, {_first_name(user)}!", purpose,
                   icon=greeting_icon(now), image="welcome")
    ui.quick_actions([
        ("Share food", ":material/add_circle:", pages["donations"], "food"),
        ("Add restaurant", ":material/add_business:", pages["restaurants"],
         "restaurant"),
        ("Add organization", ":material/domain_add:",
         pages["organizations"], "organization"),
        ("Add volunteer", ":material/person_add:", pages["volunteers"],
         "volunteer"),
    ])
    # Before the first delivery: a checklist. After it: the impact strip.
    impact = _impact(now)
    if impact and not impact.get("deliveries"):
        ui.checklist("Getting started", getting_started_steps(impact, pages))
    else:
        _impact_strip(now, impact)

    # Urgent food first: it is the one thing that cannot wait.
    if urgent:
        with ui.card("coral"):
            ui.section_title("Expiring in under 2 hours",
                             ":material/priority_high:", "coral")
            for (_, food_name, quantity, unit, expiry_time,
                 status) in urgent:
                st.markdown(
                    f"**{food_name}** · {ui.amount(quantity, unit)} · "
                    f"expires **{ui.friendly_time(expiry_time, now)}**  \n"
                    f"{ui.badge_markdown(status)}"
                )
            st.page_link(pages["pickups"], label="Arrange pickups",
                         icon=":material/arrow_forward:", width="stretch")

    ui.section_title("Today at a glance", ":material/today:", "blue")
    ui.stat_row([
        dict(label="Food available", value=counts.get("food_available", 0),
             caption="ready to request",
             zero_hint="No food waiting now.",
             icon=":material/restaurant:", tone="green",
             button_label="See food", page=pages["donations"]),
        dict(label="Urgent", value=urgent_count,
             caption="expires within 2 hours",
             zero_hint="Nothing urgent. Great job!",
             icon=":material/priority_high:", tone="red",
             button_label="See pickups", page=pages["pickups"]),
        dict(label="To accept", value=waiting_pickups,
             caption="pickup requests",
             zero_hint="All requests handled.",
             icon=":material/hourglass_top:", tone="amber",
             button_label="Accept", page=pages["pickups"]),
        dict(label="To approve", value=people_count,
             caption="people asked to join", icon=":material/person_add:",
             zero_hint="Nobody is waiting.", tone="purple",
             button_label="Review", page=pages["user-access"]),
    ])

    if orgs_count:
        with ui.card("teal"):
            st.markdown(
                f":material/verified: **{ui.plural(orgs_count, 'organization')}"
                "** waiting to be verified."
            )
            st.page_link(pages["organizations"],
                         label="Verify organizations",
                         icon=":material/arrow_forward:", width="stretch")
    if expired_count:
        st.caption(
            f"{ui.plural(expired_count, 'donation')} expired "
            "without being collected."
        )


# ---------------------------------------------------------------- donor

def _donor_home(user, my_restaurant, pages, now):
    ui.page_header(
        f"{_greeting(now)}, {_first_name(user)}!",
        "Have food to spare? Share it in a minute, and a nearby home or "
        "shelter can request it.",
        icon=greeting_icon(now), image="welcome",
    )
    _impact_strip(now)

    if not my_restaurant:
        ui.empty_state(
            "First, tell us about your kitchen",
            icon=":material/storefront:", image="signin",
            hint="Add your restaurant or kitchen once. Then you can share "
                 "food any time.",
            button_label="Add my kitchen", page=pages["my-restaurant"],
        )
        return

    if st.button("Share surplus food", type="primary",
                 icon=":material/add_circle:", width="stretch"):
        st.switch_page(pages["donations"])

    ui.section_title("My recent donations", ":material/soup_kitchen:",
                     "green")
    donations = ui.rows(get_my_donations_from_api(my_restaurant[0]),
                      "donations")
    if not donations:
        ui.empty_state(
            "You haven't shared any food yet",
            icon=":material/soup_kitchen:", image="empty-food",
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
            ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                          ":material/soup_kitchen:", "green")
            st.markdown(f"{ui.badge_markdown(shown_status)} · {when}")


# ---------------------------------------------------------------- organization

def _organization_home(user, organization, pages, now, flash_success):
    ui.page_header(
        f"{_greeting(now)}, {_first_name(user)}!",
        "Find good food for the people you serve, and follow your "
        "requests.",
        icon=greeting_icon(now), image="welcome",
    )
    _impact_strip(now)

    if not organization:
        ui.empty_state(
            "First, tell us about your organization",
            icon=":material/apartment:", image="empty-people",
            hint="A coordinator checks every organization before it can "
                 "request food.",
            button_label="Add my organization",
            page=pages["my-organization"],
        )
        return

    if not organization_is_verified(organization):
        return
    organization_id = organization[0]

    requestable_food(organization, now, flash_success)

    ui.section_title("My requests", ":material/local_shipping:", "blue")
    requests = ui.rows(
        get_pickup_requests_from_api(organization_id=organization_id),
        "pickups",
    )
    if not requests:
        st.caption("You haven't requested any food yet.")
    for pickup in requests[:5]:
        pickup_line(pickup, now, show_organization=False)
    if len(requests) > 5:
        st.page_link(pages["pickups"], label="See all my requests",
                     icon=":material/arrow_forward:")


def organization_is_verified(organization):
    """True if the organization may request food; otherwise show why not."""
    organization_name, verification = organization[1], organization[8]
    if verification == "VERIFIED":
        return True
    with ui.card():
        ui.person_header(organization_name,
                         [organization[6], organization[7]])
        st.markdown(ui.badge_markdown(verification))
        st.markdown(
            "A coordinator will check your organization. Once it is "
            "verified you can request food here."
            if verification == "PENDING" else
            "Your organization was not approved. Please contact the "
            "ministry admin."
        )
    return False


def requestable_food(organization, now, flash_success):
    """Food this organization can request now, as cards with a
    "Request this food" button. Own city first, then soonest expiry."""
    organization_id, city = organization[0], organization[6]
    food = ui.rows(get_requestable_donations_from_api(), "donations")
    same_city = (city or "").strip().lower()
    food.sort(key=lambda d: ((d[12] or "").strip().lower() != same_city,
                             d[7]))

    ui.section_title("Available food near you" if same_city
                     else "Available food", ":material/restaurant:", "green")
    if not food:
        ui.empty_state(
            "No food is waiting right now",
            icon=":material/restaurant:", image="empty-food",
            hint="New donations appear here as soon as they are shared. "
                 "Please check again later.",
        )
    for column, donation in ui.grid(food):
        with column:
            _food_card(donation, organization_id, now, flash_success)
    if st.session_state.get(_CHOSEN_FOOD):
        _request_dialog(*st.session_state[_CHOSEN_FOOD], organization_id,
                        flash_success)


def _food_card(donation, organization_id, now, flash_success):
    (donation_id, restaurant, food_name, _category, quantity, unit,
     _prepared, expiry_time, food_type, _packaging, pickup_address,
     _status, city) = donation
    food_type_words = (food_type or "").replace("_", " ").capitalize()
    with ui.card():
        ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                      ":material/restaurant:", "green")
        if food_type_words:
            st.markdown(f":gray-badge[{food_type_words}]")
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
COLLECT_CHOICES = (
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
    choices = [label for label, minutes in COLLECT_CHOICES
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
        minutes = dict(COLLECT_CHOICES)[when]
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


def pickup_line(pickup, now, show_organization=True):
    (_, food_name, quantity, unit, restaurant, organization, _requested,
     pickup_time, status, _address, _notes, volunteer_id,
     volunteer_name) = pickup[:13]
    with ui.card():
        ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                      ":material/local_shipping:", "blue")
        ui.pickup_tracker(status)
        details = [f"from {restaurant}"]
        if show_organization:
            details.append(f"to {organization}")
        if pickup_time and status not in ("DELIVERED",):
            details.append(f"pickup {ui.friendly_time(pickup_time, now)}")
        if volunteer_name and status in ("ACCEPTED", "PICKED_UP"):
            details.append(f"volunteer: {volunteer_name}")
        st.markdown(
            f"{ui.badge_markdown(ui.pickup_status(status, volunteer_id))} · "
            + " · ".join(details)
        )


# ---------------------------------------------------------------- volunteer

def _volunteer_home(user, pages, now, flash_success):
    if not user.get("volunteer_id"):
        ui.page_header(f"{_greeting(now)}, {_first_name(user)}!",
                       "Your volunteer profile is not set up yet.",
                       icon=greeting_icon(now))
        st.info("Please ask the ministry admin to finish setting up your "
                "volunteer profile.", icon=":material/info:")
        return

    # Includes the delivery address and contact, but only for this
    # volunteer's active pickups (enforced in the query).
    pickups = ui.rows(get_volunteer_pickups_from_api(user["volunteer_id"]),
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
        f"You have {ui.plural(len(today), 'pickup')} today. Thank you!"
        if today else
        "No pickups for you today. We'll assign you one when food is ready.",
        icon=greeting_icon(now), image="welcome",
    )
    _impact_strip(now)

    ui.section_title("My pickups today", ":material/directions_walk:",
                     "coral")
    if not today:
        ui.empty_state("Nothing to collect right now",
                       icon=":material/directions_walk:", image="delivery",
                       hint="We'll assign you a pickup when food is ready. "
                            "Thank you for helping!")
    first_delivery = not any(p[8] == "DELIVERED" for p in pickups)
    for number, pickup in enumerate(today, start=1):
        volunteer_card(number, pickup, now, flash_success, first_delivery)

    if later:
        ui.section_title("Coming up", ":material/event:", "purple")
        for pickup in later:
            pickup_line(pickup, now)


def volunteer_card(number, pickup, now, flash_success,
                   first_delivery=False):
    """One pickup with big buttons. first_delivery: this volunteer has not
    delivered anything yet, so their first "Delivered" gets balloons."""
    (pickup_id, food_name, quantity, unit, restaurant, organization,
     _requested, pickup_time, status, address, notes, volunteer_id,
     _name, delivery_address, delivery_contact, delivery_phone) = pickup
    when = ui.to_datetime(pickup_time)
    with ui.card():
        st.markdown(
            f"### {number}. {ui.clock_time(when).split(', ')[-1]}"
            f" · {ui.friendly_time(when, now)}"
        )
        ui.pickup_tracker(status)
        st.markdown(ui.badge_markdown(ui.pickup_status(status,
                                                       volunteer_id)))
        st.markdown(
            f":material/restaurant: **{food_name}** · "
            f"{ui.amount(quantity, unit)}  \n"
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
            elif new_status == "DELIVERED":
                flash_success(done, toast=f"{food_name} delivered. Thank "
                                          "you for serving!",
                              celebrate=first_delivery)
            else:
                flash_success(done)
