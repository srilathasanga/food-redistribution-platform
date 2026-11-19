"""Pickup requests (admin, organization) and My pickups (volunteer).

Who may do what here:
    admin         sees everything; accepts requests, assigns volunteers,
                  can mark pickups picked up / delivered, and can request
                  food on an organization's behalf
    organization  sees only its own requests
    volunteer     sees only pickups assigned to them (with the delivery
                  address and contact only while the pickup is active)
"""

from datetime import timedelta

import streamlit as st

from app import ui
from app.backend import (
    assign_volunteer_to_pickup_from_api,
    create_pickup_from_api,
    get_pickup_requests_from_api,
    get_requestable_donations_from_api,
    get_verified_organizations_from_api,
    get_volunteer_pickups_from_api,
    get_volunteers_from_api,
    update_pickup_status_from_api,
)
from app.home_pages import (
    ACTIVE_FOR_VOLUNTEER,
    COLLECT_CHOICES,
    pickup_line,
    volunteer_card,
)
from app.timeutil import now_local


def pickups_page(ctx):
    now = now_local()
    if ctx.role == "VOLUNTEER":
        _volunteer_pickups(ctx, now)
    elif ctx.role == "ORGANIZATION":
        _organization_pickups(ctx, now)
    else:
        _admin_pickups(ctx, now)


# ---------------------------------------------------------------- volunteer

def _volunteer_pickups(ctx, now):
    ui.page_header("My pickups",
                   "Collect the food, then deliver it. Tap the big button "
                   "after each step.",
                   icon=":material/local_shipping:")
    if not ctx.user["volunteer_id"]:
        st.info("Please ask the ministry admin to finish setting up your "
                "volunteer profile.", icon=":material/info:")
        return
    pickups = ui.rows(get_volunteer_pickups_from_api(ctx.user["volunteer_id"]),
                      "pickups")
    active = [p for p in pickups if p[8] in ACTIVE_FOR_VOLUNTEER]
    finished = [p for p in pickups if p[8] not in ACTIVE_FOR_VOLUNTEER]

    if not active:
        ui.empty_state("No pickups assigned to you right now",
                       icon=":material/directions_walk:", image="delivery",
                       hint="A coordinator assigns pickups when food is "
                            "ready. Thank you for helping!")
    # Balloons only for this volunteer's very first delivery.
    first_delivery = not any(p[8] == "DELIVERED" for p in finished)
    for number, pickup in enumerate(active, start=1):
        volunteer_card(number, pickup, now, ui.flash_success, first_delivery)

    if finished:
        with st.expander(f"Finished ({len(finished)})",
                         icon=":material/task_alt:"):
            for pickup in reversed(finished[-20:]):
                pickup_line(pickup, now)


# ---------------------------------------------------------------- organization

def _organization_pickups(ctx, now):
    ui.page_header("Pickup requests",
                   "Follow the food you asked for, from request to "
                   "delivery.",
                   icon=":material/local_shipping:")
    organization = ctx.my_organization
    if not organization or organization[8] != "VERIFIED":
        st.warning("Your organization must be registered and verified "
                   "before it can request food.",
                   icon=":material/hourglass_top:")
        return

    if st.button("Find food to request", type="primary",
                 icon=":material/restaurant:", width="stretch"):
        st.switch_page(ctx.pages["available-food"])

    requests = ui.rows(get_pickup_requests_from_api(
        organization_id=organization[0]), "pickups")
    if not requests:
        ui.empty_state("No pickup requests yet",
                       icon=":material/local_shipping:", image="empty-list",
                       hint="Request food from Available food and follow "
                            "it here.")
    for column, pickup in ui.grid(requests):
        with column:
            pickup_line(pickup, now, show_organization=False)


# ---------------------------------------------------------------- admin

def _admin_pickups(ctx, now):
    pickups = ui.rows(get_pickup_requests_from_api(), "pickups")
    to_accept = [p for p in pickups if p[8] == "REQUESTED"]
    needs_volunteer = [p for p in pickups
                       if p[8] == "ACCEPTED" and p[11] is None]
    on_the_way = [p for p in pickups
                  if (p[8] == "ACCEPTED" and p[11] is not None)
                  or p[8] == "PICKED_UP"]
    delivered = [p for p in pickups if p[8] == "DELIVERED"]

    waiting = len(to_accept) + len(needs_volunteer)
    ui.page_header(
        "Pickup requests",
        "Accept each request, then choose a volunteer. "
        + (f"{ui.plural(waiting, 'pickup')} waiting for you."
           if waiting else "Nothing is waiting for you."),
        icon=":material/local_shipping:",
    )

    # 1. Accept
    ui.section_title(f"1. To accept ({len(to_accept)})",
                     ":material/inbox:", "coral")
    if not to_accept:
        st.caption("No new requests.")
    for column, pickup in ui.grid(to_accept):
        with column, ui.card():
            _pickup_details(pickup, now)
            if st.button("Accept", key=f"accept_{pickup[0]}",
                         type="primary", icon=":material/check:",
                         width="stretch"):
                _change_status(pickup, "ACCEPTED",
                               f"Accepted {pickup[1]}. Next: choose a "
                               "volunteer under \"Needs a volunteer\".")

    # 2. Assign a volunteer
    ui.section_title(f"2. Needs a volunteer ({len(needs_volunteer)})",
                     ":material/person_search:", "purple")
    volunteers = []
    if needs_volunteer:
        volunteers = [
            v for v in ui.rows(get_volunteers_from_api(), "volunteers")
            if v[6] == "AVAILABLE" and v[7] == "ACTIVE"
        ]
    else:
        st.caption("Every accepted pickup has a volunteer.")
    for column, pickup in ui.grid(needs_volunteer):
        with column, ui.card():
            _pickup_details(pickup, now)
            if not volunteers:
                st.info("No volunteer is free right now. Volunteers become "
                        "free again after they deliver.",
                        icon=":material/info:")
                continue
            by_id = {v[0]: v for v in volunteers}
            chosen = st.selectbox(
                "Volunteer", list(by_id), key=f"volunteer_{pickup[0]}",
                format_func=lambda vid: (
                    f"{by_id[vid][1]}"
                    + (f" ({by_id[vid][5]})" if by_id[vid][5] else "")),
            )
            if st.button("Assign volunteer",
                         key=f"assign_volunteer_{pickup[0]}",
                         type="primary", icon=":material/directions_walk:",
                         width="stretch"):
                result = assign_volunteer_to_pickup_from_api(pickup[0],
                                                             chosen)
                if "error" in result:
                    st.error(result["error"], icon=":material/error:")
                else:
                    ui.flash_success(
                        f"Volunteer assigned: {by_id[chosen][1]} will "
                        f"collect {pickup[1]}. They will see it on their "
                        "Home page."
                    )

    # 3. On the way
    ui.section_title(f"3. On the way ({len(on_the_way)})",
                     ":material/local_shipping:", "blue")
    if not on_the_way:
        st.caption("Nothing is on the way right now.")
    for column, pickup in ui.grid(on_the_way):
        with column, ui.card():
            _pickup_details(pickup, now)
            if pickup[8] == "ACCEPTED":
                if st.button("Mark picked up", key=f"pickedup_{pickup[0]}",
                             icon=":material/local_shipping:",
                             width="stretch"):
                    _change_status(pickup, "PICKED_UP",
                                   f"{pickup[1]} is picked up. Next: "
                                   f"delivery to {pickup[5]}.")
            elif st.button("Mark delivered", key=f"delivered_{pickup[0]}",
                           icon=":material/task_alt:", width="stretch"):
                _change_status(pickup, "DELIVERED",
                               f"{pickup[1]} was delivered to {pickup[5]}. "
                               "Thank you!",
                               toast=f"{pickup[1]} delivered!",
                               celebrate=not delivered)

    # 4. Delivered
    with st.expander(f"4. Delivered ({len(delivered)})",
                     icon=":material/task_alt:"):
        if not delivered:
            st.caption("Nothing delivered yet.")
        for pickup in delivered[:30]:
            pickup_line(pickup, now)

    _request_for_organization()


def _pickup_details(pickup, now):
    (_, food_name, quantity, unit, restaurant, organization, _requested,
     pickup_time, status, address, notes, volunteer_id,
     volunteer_name) = pickup[:13]
    ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                  ":material/local_shipping:", "blue")
    ui.pickup_tracker(status)
    st.markdown(ui.badge_markdown(ui.pickup_status(status, volunteer_id)))
    lines = [f":material/storefront: From **{restaurant}**",
             f":material/home: To **{organization}**"]
    if pickup_time:
        lines.append(f":material/schedule: Pickup "
                     f"{ui.friendly_time(pickup_time, now)} "
                     f"({ui.clock_time(pickup_time)})")
    if address:
        lines.append(f":material/location_on: {address}")
    if volunteer_name:
        lines.append(f":material/directions_walk: {volunteer_name}")
    if notes:
        lines.append(f":material/sticky_note_2: {notes}")
    st.markdown("  \n".join(lines))


def _change_status(pickup, new_status, message, toast=None,
                   celebrate=False):
    result = update_pickup_status_from_api(pickup[0], new_status)
    if "error" in result:
        st.error(result["error"], icon=":material/error:")
    else:
        ui.flash_success(message, toast=toast, celebrate=celebrate)


def _request_for_organization():
    """Admins can request food on an organization's behalf."""
    with st.expander("Request food for an organization",
                     icon=":material/add_circle:"):
        food = ui.rows(get_requestable_donations_from_api(), "donations")
        organizations = ui.rows(get_verified_organizations_from_api(),
                                "organizations")
        if not food:
            st.caption("No food is waiting to be requested.")
            return
        if not organizations:
            st.caption("No verified organizations yet.")
            return
        food_by_id = {row[0]: row for row in food}
        organization_by_id = {row[0]: row for row in organizations}
        with st.form("admin_request_form"):
            donation_id = st.selectbox(
                "Food", list(food_by_id),
                format_func=lambda i: (
                    f"{food_by_id[i][2]} · "
                    f"{ui.amount(food_by_id[i][4], food_by_id[i][5])} "
                    f"from {food_by_id[i][1]}"),
            )
            organization_id = st.selectbox(
                "For which organization?", list(organization_by_id),
                format_func=lambda i: organization_by_id[i][1],
            )
            when = st.radio("When can a volunteer collect it?",
                            [label for label, _ in COLLECT_CHOICES])
            notes = st.text_input("Note for the volunteer (optional)")
            if st.form_submit_button("Send request", type="primary",
                                     icon=":material/send:",
                                     width="stretch"):
                donation = food_by_id[donation_id]
                pickup_time = now_local() + timedelta(
                    minutes=dict(COLLECT_CHOICES)[when])
                if pickup_time >= ui.to_datetime(donation[7]):
                    st.error("That is after the food expires. Please "
                             "choose an earlier time.",
                             icon=":material/error:")
                    return
                result = create_pickup_from_api({
                    "donation_id": donation_id,
                    "organization_id": organization_id,
                    "pickup_time": pickup_time.isoformat(),
                    "pickup_address": donation[10],
                    "notes": notes.strip() or None,
                })
                if "error" in result:
                    st.error(result["error"], icon=":material/error:")
                else:
                    ui.flash_success(
                        f"Requested {donation[2]} for "
                        f"{organization_by_id[organization_id][1]}. Next: "
                        "accept it above and choose a volunteer."
                    )
