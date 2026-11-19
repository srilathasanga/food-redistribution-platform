"""Pickup requests (admin, organization) and My pickups (volunteer).

Who may do what here:
    admin         sees everything; accepts requests, assigns volunteers,
                  can mark pickups picked up / delivered, and can request
                  food on an organization's behalf
    organization  sees only its own requests
    volunteer     sees only pickups assigned to them (with the delivery
                  address and contact only while the pickup is active)
"""

import streamlit as st

from app import ui
from app.backend import (
    assign_volunteer_to_pickup_from_api,
    create_pickup_from_api,
    get_available_donations_from_api,
    get_pickup_requests_from_api,
    get_verified_organizations_from_api,
    get_volunteer_pickups_from_api,
    get_volunteers_from_api,
    update_pickup_status_from_api,
)
from app.home_pages import (
    ACTIVE_FOR_VOLUNTEER,
    pickup_line,
    volunteer_card,
)
from app.timeutil import now_local

flash_success = ui.flash_success


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
                       icon=":material/directions_walk:",
                       hint="A coordinator assigns pickups when food is "
                            "ready. Thank you for helping!")
    for number, pickup in enumerate(active, start=1):
        volunteer_card(number, pickup, now, ui.flash_success)

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
                       icon=":material/local_shipping:",
                       hint="Request food from Available food and follow "
                            "it here.")
    for column, pickup in ui.grid(requests):
        with column:
            pickup_line(pickup, now, show_organization=False)


# ---------------------------------------------------------------- admin

def _admin_pickups(ctx, now):
    # Old admin view; regrouped by next action in a later change.
    user = ctx.user
    role = ctx.role
    is_admin = ctx.is_admin

    st.header(
        "🚚 My Pickups" if role == "VOLUNTEER" else "🚚 Pickup Requests"
    )

    # Who may do what on this page:
    #   admin         everything
    #   volunteer     sees only pickups assigned to them; marks them
    #                 picked up and delivered
    #   organization  sees only its own pickups; requests new ones
    can_accept = is_admin
    can_assign = is_admin
    can_progress = is_admin or role == "VOLUNTEER"
    can_request = is_admin or role == "ORGANIZATION"

    # -----------------------------------------------------
    # PICKUP REQUEST DASHBOARD
    # -----------------------------------------------------

    st.subheader("📋 Pickup Request Dashboard")

    try:

        if role == "ORGANIZATION":
            pickup_response = get_pickup_requests_from_api(
                organization_id=user["organization_id"] or -1
            )
        elif role == "VOLUNTEER":
            pickup_response = get_pickup_requests_from_api(
                volunteer_id=user["volunteer_id"] or -1
            )
        else:
            pickup_response = get_pickup_requests_from_api()

        if "error" in pickup_response:

            st.error(
                pickup_response["error"]
            )

            pickup_requests = []

        else:

            pickup_requests = (
                pickup_response["pickups"]
            )

        volunteers = []

        if can_assign:

            volunteer_response = get_volunteers_from_api()

            if "error" in volunteer_response:

                st.error(
                    volunteer_response["error"]
                )

            else:

                volunteers = (
                    volunteer_response["volunteers"]
                )

        if not pickup_requests:

            st.info(
                "No pickups assigned to you yet."
                if role == "VOLUNTEER"
                else "No pickup requests found."
            )

        else:

            for pickup in pickup_requests:

                pickup_id = pickup[0]
                food_name = pickup[1]
                quantity = pickup[2]
                unit = pickup[3]
                restaurant_name = pickup[4]
                organization_name = pickup[5]
                requested_at = pickup[6]
                pickup_time = pickup[7]
                pickup_status = pickup[8]
                pickup_address = pickup[9]
                notes = pickup[10]
                volunteer_id = pickup[11]
                volunteer_name = pickup[12]

                with st.expander(
                    f"Pickup #{pickup_id} | "
                    f"{food_name} | "
                    f"Status: {pickup_status}"
                ):

                    st.write(
                        f"**Food:** {food_name} "
                        f"({quantity} {unit})"
                    )

                    st.write(
                        f"**Restaurant:** "
                        f"{restaurant_name}"
                    )

                    st.write(
                        f"**Organization:** "
                        f"{organization_name}"
                    )

                    st.write(
                        f"**Pickup Status:** "
                        f"{pickup_status}"
                    )

                    st.write(
                        f"**Requested At:** "
                        f"{str(requested_at).replace('T', ' ')[:16]}"
                    )

                    st.write(
                        f"**Pickup Time:** "
                        f"{str(pickup_time).replace('T', ' ')[:16]}"
                    )

                    st.write(
                        f"**Pickup Address:** "
                        f"{pickup_address}"
                    )

                    st.write(
                        f"**Notes:** {notes}"
                    )

                    # -------------------------------------
                    # VOLUNTEER ASSIGNMENT
                    # -------------------------------------

                    if volunteer_id is not None:

                        st.success(
                            f"👤 Assigned Volunteer: "
                            f"{volunteer_name}"
                        )

                    elif not can_assign:

                        st.write("**Volunteer:** not assigned yet")

                    elif pickup_status != "ACCEPTED":

                        st.caption(
                            "Accept this pickup first, "
                            "then assign a volunteer."
                        )

                    else:

                        available_volunteers = [
                            volunteer
                            for volunteer in volunteers
                            if volunteer[6] == "AVAILABLE"
                            and volunteer[7] == "ACTIVE"
                        ]

                        if available_volunteers:

                            volunteer_options = {
                                f"{volunteer[1]} - "
                                f"{volunteer[2]}":
                                volunteer[0]
                                for volunteer
                                in available_volunteers
                            }

                            selected_volunteer = (
                                st.selectbox(
                                    "Assign Volunteer",
                                    options=list(
                                        volunteer_options.keys()
                                    ),
                                    key=(
                                        f"volunteer_{pickup_id}"
                                    )
                                )
                            )

                            if st.button(
                                "Assign Volunteer",
                                key=(
                                    f"assign_volunteer_"
                                    f"{pickup_id}"
                                )
                            ):

                                selected_id = (
                                    volunteer_options[
                                        selected_volunteer
                                    ]
                                )

                                result = (
                                    assign_volunteer_to_pickup_from_api(
                                        pickup_id,
                                        selected_id
                                    )
                                )

                                if "error" in result:

                                    st.error(
                                        result["error"]
                                    )

                                else:

                                    flash_success(
                                        "Volunteer assigned successfully! "
                                        f"Volunteer ID: {selected_id}"
                                    )

                        else:

                            st.info(
                                "No active and available volunteers "
                                "are currently available."
                            )

                    st.divider()

                    # -------------------------------------
                    # REQUESTED → ACCEPTED
                    # -------------------------------------

                    if pickup_status == "REQUESTED" and can_accept:

                        if st.button(
                            "✅ Accept Pickup",
                            key=f"accept_{pickup_id}"
                        ):

                            result = (
                                update_pickup_status_from_api(
                                    pickup_id,
                                    "ACCEPTED"
                                )
                            )

                            if "error" in result:

                                st.error(
                                    f"Error accepting pickup: "
                                    f"{result['error']}"
                                )

                            else:

                                flash_success(
                                    f"Pickup "
                                    f"#{result['pickup_id']} "
                                    f"accepted successfully!"
                                )

                    # -------------------------------------
                    # ACCEPTED → PICKED_UP
                    # -------------------------------------

                    elif pickup_status == "ACCEPTED" and can_progress:

                        if st.button(
                            "📦 Mark Picked Up",
                            key=f"pickedup_{pickup_id}"
                        ):

                            result = (
                                update_pickup_status_from_api(
                                    pickup_id,
                                    "PICKED_UP"
                                )
                            )

                            if "error" in result:

                                st.error(
                                    f"Error marking pickup: "
                                    f"{result['error']}"
                                )

                            else:

                                flash_success(
                                    f"Pickup "
                                    f"#{result['pickup_id']} "
                                    f"marked as PICKED_UP!"
                                )

                    # -------------------------------------
                    # PICKED_UP → DELIVERED
                    # -------------------------------------

                    elif pickup_status == "PICKED_UP" and can_progress:

                        if st.button(
                            "🚚 Mark Delivered",
                            key=f"delivered_{pickup_id}"
                        ):

                            result = (
                                update_pickup_status_from_api(
                                    pickup_id,
                                    "DELIVERED"
                                )
                            )

                            if "error" in result:

                                st.error(
                                    f"Error marking delivery: "
                                    f"{result['error']}"
                                )

                            else:

                                flash_success(
                                    f"Pickup "
                                    f"#{result['pickup_id']} "
                                    f"marked as DELIVERED!"
                                )

                    # -------------------------------------
                    # DELIVERED
                    # -------------------------------------

                    elif pickup_status == "DELIVERED":

                        st.success(
                            "✅ Delivery completed"
                        )

    except Exception as e:

        st.error(
            f"Error loading pickup requests: {e}"
        )

    # -----------------------------------------------------
    # REQUEST PICKUP
    # -----------------------------------------------------

    if not can_request:
        st.stop()

    st.divider()

    st.subheader("🚚 Request Pickup")

    donation_response = (
        get_available_donations_from_api()
    )

    if "error" in donation_response:

        st.error(
            donation_response["error"]
        )

        available_donations = []

    else:

        donations = donation_response["donations"]

        available_donations = [
            tuple(donation)
            for donation in donations
        ]

    if not available_donations:

        st.info(
            "No available food donations."
        )

    else:

        donation_options = {
            f"#{row[0]} {row[2]} ({row[4]} {row[5]}) from {row[1]}, "
            f"expires {str(row[7]).replace('T', ' ')[:16]}":
            row[0]
            for row in available_donations
        }
        donation_addresses = {
            row[0]: row[10] or "" for row in available_donations
        }

        selected_donation = st.selectbox(
            "Select Food Donation",
            list(donation_options.keys())
        )

        donation_id = donation_options[
            selected_donation
        ]

        organization_response = (
            get_verified_organizations_from_api()
        )

        if "error" in organization_response:

            st.error(
                organization_response["error"]
            )

            verified_organizations = []

        else:

            organizations = (
                organization_response["organizations"]
            )

            verified_organizations = [
                tuple(organization)
                for organization in organizations
            ]

        if role == "ORGANIZATION":
            # An organization can only request food for itself.
            verified_organizations = [
                row for row in verified_organizations
                if row[0] == user["organization_id"]
            ]

        if not verified_organizations:

            st.warning(
                "Your organization must be registered and verified "
                "before it can request food."
                if role == "ORGANIZATION"
                else "No verified organizations available."
            )

        else:

            organization_options = {
                f"{row[0]} - {row[1]}":
                row[0]
                for row in verified_organizations
            }

            selected_organization = st.selectbox(
                "Select Organization",
                list(organization_options.keys())
            )

            organization_id = organization_options[
                selected_organization
            ]

            pickup_date = st.date_input(
                "Pickup Date",
                value=now_local().date()
            )

            pickup_time_input = st.time_input(
                "Pickup Time"
            )

            pickup_address = st.text_input(
                "Pickup Address",
                value=donation_addresses.get(donation_id, ""),
                key=f"pickup_address_{donation_id}"
            )

            notes = st.text_area(
                "Notes"
            )

            if st.button(
                "🚚 Request Pickup"
            ):

                try:

                    from datetime import datetime

                    pickup_datetime = datetime.combine(
                        pickup_date,
                        pickup_time_input
                    )

                    pickup_data = {
                        "donation_id": donation_id,
                        "organization_id": organization_id,
                        "pickup_time": (
                            pickup_datetime.isoformat()
                        ),
                        "pickup_address": pickup_address,
                        "notes": notes
                    }

                    result = create_pickup_from_api(
                        pickup_data
                    )

                    if "error" in result:

                        st.error(
                            f"Error creating pickup: "
                            f"{result['error']}"
                        )

                    else:

                        flash_success(
                            f"Pickup request created successfully! "
                            f"Pickup ID: {result['pickup_id']}"
                        )

                except Exception as e:

                    st.error(
                        str(e)
                    )
