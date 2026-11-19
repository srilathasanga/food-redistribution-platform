import logging

import psycopg2
import streamlit as st

from app.auth import ROLE_LABELS, logout_button, require_user
from app.backend import (
    assign_volunteer_to_pickup_from_api,
    create_donation_from_api,
    create_organization_from_api,
    create_pickup_from_api,
    create_restaurant_from_api,
    create_volunteer_from_api,
    get_available_donations_from_api,
    get_donation_summary_from_api,
    get_food_risk_analysis_from_api,
    get_organization_summary_from_api,
    get_pending_organizations_from_api,
    get_pickup_requests_from_api,
    get_pickup_summary_from_api,
    get_restaurants_from_api,
    get_verified_organizations_from_api,
    get_volunteer_summary_from_api,
    get_volunteers_from_api,
    reject_organization_from_api,
    update_pickup_status_from_api,
    verify_organization_from_api,
)
from app.database import is_configured
from app.navigation import MENU, PAGES, pages_for, title_for
from app.privacy import (
    is_privacy_request,
    privacy_link_markdown,
    render_privacy_page,
)
from app.schema import ensure_schema
from app.timeutil import now_local
from app.ui import apply_style
from app.user_service import (
    ROLES,
    approve_user,
    get_organization,
    get_restaurant,
    link_organization,
    link_restaurant,
    list_users,
    set_user_status,
)


# =========================================================
# STREAMLIT PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Food Redistribution Platform",
    page_icon="🍲",
    layout="wide"
)

apply_style()


# Public privacy policy (?page=privacy). It must work without login and
# without the database, so it runs before both.
if is_privacy_request():
    render_privacy_page()
    st.stop()


@st.cache_resource(show_spinner="Preparing the database...")
def prepare_database():
    # Creates any missing tables once per server start.
    ensure_schema()
    return True


logger = logging.getLogger("food_app")


def database_unavailable_screen(show_title=True):
    """Friendly message instead of a Python traceback. Stops the page."""
    if show_title:
        st.title("🍲 Food Redistribution Platform")
    st.error(
        "We can't reach the app's database right now, so the app is "
        "paused. Your information is safe.",
        icon=":material/cloud_off:",
    )
    st.markdown(
        "**Please try again in a minute.** If it keeps happening, tell "
        "the ministry admin."
    )
    if st.button("Try again", type="primary"):
        st.rerun()
    with st.expander("For the admin: how to fix this"):
        if not is_configured():
            st.markdown(
                "No database is set up. Add `DATABASE_URL` (the Neon "
                "connection string) to the Streamlit secrets, or to `.env` "
                "on your own computer."
            )
        else:
            st.markdown(
                "- Check that `DATABASE_URL` in the Streamlit secrets is "
                "correct (copy it again from the Neon dashboard).\n"
                "- Check that the Neon project is running.\n"
                "- The exact error is in the app logs (Streamlit Cloud: "
                "**Manage app** → logs)."
            )
    st.caption(privacy_link_markdown())
    st.stop()


try:
    prepare_database()
except Exception:
    # Not cached when it fails, so the next visit tries again.
    logger.exception("Could not prepare the database")
    database_unavailable_screen()


def flash_success(message):
    """Show a success message after the page refreshes with fresh data."""
    st.session_state["flash"] = message
    st.rerun()


st.title("🍲 Food Redistribution Platform")

st.write(
    "Connecting surplus food from restaurants "
    "with verified organizations for redistribution."
)


# =========================================================
# LOGIN
# =========================================================

try:
    user = require_user()
except psycopg2.Error:
    logger.exception("Database error while signing in")
    database_unavailable_screen(show_title=False)
role = user["role"]
is_admin = role == "ADMIN"

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))


my_restaurant = (
    get_restaurant(user["restaurant_id"])
    if user["restaurant_id"] else None
)
my_organization = (
    get_organization(user["organization_id"])
    if user["organization_id"] else None
)


# =========================================================
# HOME
# =========================================================

def home_page():

    st.header(f"Welcome, {user['full_name'] or user['email']}")
    st.caption(ROLE_LABELS[role])

    if is_admin:
        pending_users = list_users(status="PENDING")
        pending_orgs = get_pending_organizations_from_api()
        col1, col2 = st.columns(2)
        col1.metric("People waiting for access", len(pending_users))
        col2.metric(
            "Organizations waiting for verification",
            len(pending_orgs.get("organizations", [])),
        )
        st.info(
            "Approve people under **User access**, verify organizations "
            "under **Reports & tools**, and assign volunteers under "
            "**Pickup requests**."
        )

    elif role == "DONOR":
        if my_restaurant:
            st.info(
                f"You donate as **{my_restaurant[1]}**. "
                "Post surplus food under **My donations**."
            )
        else:
            st.warning(
                "First register your restaurant or kitchen under "
                "**My restaurant**, then post food under **My donations**."
            )

    elif role == "ORGANIZATION":
        if not my_organization:
            st.warning(
                "Register your organization under **My organization**. "
                "An admin will verify it before you can request food."
            )
        elif my_organization[8] == "VERIFIED":
            st.success(
                f"**{my_organization[1]}** is verified. See **Available food** "
                "and request a pickup under **Pickup requests**."
            )
        else:
            st.info(
                f"**{my_organization[1]}** is "
                f"{my_organization[8].lower()} verification."
            )

    elif role == "VOLUNTEER":
        st.info(
            "Your assigned pickups are under **My pickups**. Mark each one "
            "picked up and then delivered as you go."
        )


# =========================================================
# MY RESTAURANT (donor)
# =========================================================

def my_restaurant_page():

    st.header("🏪 My Restaurant")

    if my_restaurant:
        st.write(f"**Name:** {my_restaurant[1]}")
        st.write(f"**Contact person:** {my_restaurant[2]}")
        st.write(f"**Phone:** {my_restaurant[3]}")
        st.write(f"**Email:** {my_restaurant[4]}")
        st.write(f"**Address:** {my_restaurant[5]}")
        st.write(f"**City:** {my_restaurant[6]}")
        st.caption("To change these details, please contact an admin.")
    else:
        st.write("Register the restaurant or kitchen you donate from.")
        with st.form("my_restaurant_form"):
            restaurant_name = st.text_input("Restaurant / kitchen name")
            contact_person = st.text_input(
                "Contact person", value=user["full_name"] or ""
            )
            phone = st.text_input("Phone", value=user["phone"] or "")
            email = st.text_input("Email", value=user["email"])
            address = st.text_area("Address")
            city = st.text_input("City", value=user["city"] or "")
            if st.form_submit_button("Register", type="primary"):
                if not restaurant_name.strip():
                    st.error("Name is required.")
                else:
                    result = create_restaurant_from_api({
                        "restaurant_name": restaurant_name,
                        "contact_person": contact_person,
                        "phone": phone,
                        "email": email,
                        "address": address,
                        "city": city,
                    })
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        link_restaurant(
                            user["email"], result["restaurant_id"]
                        )
                        flash_success(
                            "Registered! You can now post food donations."
                        )


# =========================================================
# MY ORGANIZATION (receiving organization)
# =========================================================

def my_organization_page():

    st.header("🏢 My Organization")

    if my_organization:
        st.write(f"**Name:** {my_organization[1]}")
        st.write(f"**Type:** {my_organization[7]}")
        st.write(f"**Contact person:** {my_organization[2]}")
        st.write(f"**Phone:** {my_organization[3]}")
        st.write(f"**Address:** {my_organization[5]}, {my_organization[6]}")
        status = my_organization[8]
        if status == "VERIFIED":
            st.success("Verified. You can request food pickups.")
        elif status == "REJECTED":
            st.error(
                "Not approved. Reason: "
                f"{my_organization[10] or 'not given'}. "
                "Please contact an admin."
            )
        else:
            st.info("Waiting for an admin to verify your organization.")
    else:
        st.write("Register the organization that will receive food.")
        with st.form("my_organization_form"):
            organization_name = st.text_input("Organization name")
            contact_person = st.text_input(
                "Contact person", value=user["full_name"] or ""
            )
            phone = st.text_input("Phone", value=user["phone"] or "")
            email = st.text_input("Email", value=user["email"])
            address = st.text_area("Address")
            city = st.text_input("City", value=user["city"] or "")
            organization_type = st.selectbox(
                "Organization type",
                ["NGO", "Charity", "Food Bank",
                 "Community Organization", "Other"],
            )
            if st.form_submit_button("Register", type="primary"):
                if not organization_name.strip():
                    st.error("Organization name is required.")
                else:
                    result = create_organization_from_api({
                        "organization_name": organization_name,
                        "contact_person": contact_person,
                        "phone": phone,
                        "email": email,
                        "address": address,
                        "city": city,
                        "organization_type": organization_type,
                    })
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        link_organization(
                            user["email"], result["organization_id"]
                        )
                        flash_success(
                            "Registered! An admin will verify your "
                            "organization soon."
                        )


# =========================================================
# AVAILABLE FOOD (receiving organization)
# =========================================================

def available_food_page():

    st.header("🍱 Available Food")
    donation_response = get_available_donations_from_api()
    if "error" in donation_response:
        st.error(donation_response["error"])
    elif donation_response["donations"]:
        for donation in donation_response["donations"]:
            st.write(
                f"**{donation[2]}** — {donation[4]} {donation[5]} — "
                f"{donation[1]} — {donation[8].replace('_', ' ').title()} — "
                f"Expires: {donation[7].replace('T', ' ')[:16]}"
            )
        st.caption("Request any of these under **Pickup requests**.")
    else:
        st.info("No food is available right now. Please check back later.")


# =========================================================
# USER ACCESS (admin)
# =========================================================

def user_access_page():

    st.header("🔐 User Access")

    st.subheader("Waiting for approval")
    pending_users = list_users(status="PENDING")
    if not pending_users:
        st.success("Nobody is waiting. ✅")
    for person in pending_users:
        with st.container(border=True):
            st.write(
                f"**{person['full_name']}** · {person['email']} · "
                f"{person['phone'] or 'no phone'} · {person['city'] or ''}"
            )
            st.caption(f"Asked to join as {person['role'].title()}")
            col1, col2, col3 = st.columns([2, 1, 1])
            chosen_role = col1.selectbox(
                "Role",
                ROLES,
                index=ROLES.index(person["role"]),
                key=f"role_{person['email']}",
                label_visibility="collapsed",
            )
            if col2.button("Approve", key=f"approve_{person['email']}",
                           type="primary"):
                try:
                    approve_user(person["email"], chosen_role)
                    flash_success(
                        f"{person['email']} approved as {chosen_role.title()}."
                    )
                except ValueError as error:
                    st.error(str(error))
            if col3.button("Decline", key=f"decline_{person['email']}"):
                set_user_status(person["email"], "DISABLED")
                flash_success(f"{person['email']} declined.")

    st.divider()
    st.subheader("All users")
    everyone = list_users()
    st.dataframe(
        [
            {
                "Email": person["email"],
                "Name": person["full_name"],
                "Role": person["role"].title(),
                "Status": person["status"].title(),
                "Last login": person["last_login_at"],
            }
            for person in everyone
        ],
        hide_index=True,
        use_container_width=True,
    )

    active_others = [
        person for person in everyone
        if person["email"] != user["email"]
    ]
    if active_others:
        st.write("**Change someone's access**")
        col1, col2, col3 = st.columns([3, 2, 1])
        target_email = col1.selectbox(
            "User", [person["email"] for person in active_others]
        )
        new_status = col2.selectbox("Status", ["ACTIVE", "DISABLED"])
        if col3.button("Save", key="save_status"):
            set_user_status(target_email, new_status)
            flash_success(f"{target_email} is now {new_status.lower()}.")


def restaurants_page():

    st.header("🏪 Restaurant Management")

    st.subheader("Add Restaurant")

    with st.form("restaurant_form"):

        restaurant_name = st.text_input(
            "Restaurant Name"
        )

        contact_person = st.text_input(
            "Contact Person"
        )

        phone = st.text_input(
            "Phone"
        )

        email = st.text_input(
            "Email"
        )

        address = st.text_area(
            "Address"
        )

        city = st.text_input(
            "City"
        )

        submitted = st.form_submit_button(
            "Add Restaurant"
        )

        if submitted:

            if not restaurant_name.strip():

                st.error(
                    "Restaurant name is required."
                )

            else:

                restaurant_data = {
                    "restaurant_name": restaurant_name,
                    "contact_person": contact_person,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "city": city
                }

                result = create_restaurant_from_api(
                    restaurant_data
                )

                if "error" in result:

                    st.error(
                        f"Error creating restaurant: "
                        f"{result['error']}"
                    )

                else:

                    flash_success(
                        f"Restaurant created successfully! "
                        f"Restaurant ID: "
                        f"{result['restaurant_id']}"
                    )

    st.divider()

    st.subheader("Registered Restaurants")

    restaurant_response = get_restaurants_from_api()

    if "error" in restaurant_response:

        st.error(
            restaurant_response["error"]
        )

    else:

        restaurants = restaurant_response["restaurants"]

        if restaurants:

            for restaurant in restaurants:

                st.write(
                    f"**{restaurant[1]}** — "
                    f"{restaurant[6]} "
                    f"(ID: {restaurant[0]})"
                )

        else:

            st.info(
                "No restaurants registered yet."
            )


# =========================================================
# FOOD DONATIONS
# =========================================================

def donations_page():

    st.header("🍱 Food Donation Management")

    st.subheader("Create Food Donation")

    restaurant_response = get_restaurants_from_api()

    if "error" in restaurant_response:

        st.error(
            restaurant_response["error"]
        )

        restaurants = []

    else:

        restaurants = restaurant_response["restaurants"]

    if not is_admin:
        # A donor can only post food for their own restaurant.
        restaurants = [
            restaurant for restaurant in restaurants
            if restaurant[0] == user["restaurant_id"]
        ]

    if not restaurants:

        st.warning(
            "No restaurants are available. "
            "Please register a restaurant first"
            + (" under **My restaurant**." if not is_admin else ".")
        )

    else:

        restaurant_options = {
            f"{restaurant[1]} (ID: {restaurant[0]})":
            restaurant[0]
            for restaurant in restaurants
        }

        selected_restaurant = st.selectbox(
            "Restaurant",
            list(restaurant_options.keys())
        )

        restaurant_id = restaurant_options[
            selected_restaurant
        ]

        with st.form("donation_form"):

            food_name = st.text_input(
                "Food Name"
            )

            food_category = st.text_input(
                "Food Category"
            )

            quantity = st.number_input(
                "Quantity",
                min_value=0.01,
                step=0.5
            )

            unit = st.selectbox(
                "Unit",
                [
                    "kg",
                    "litres",
                    "packets",
                    "boxes",
                    "plates"
                ]
            )

            prepared_date = st.date_input(
                "Prepared Date",
                value=now_local().date()
            )

            prepared_time = st.time_input(
                "Prepared Time"
            )

            expiry_date = st.date_input(
                "Expiry Date",
                value=now_local().date()
            )

            expiry_time = st.time_input(
                "Expiry Time"
            )

            food_type = st.selectbox(
                "Food Type",
                [
                    "VEGETARIAN",
                    "NON_VEGETARIAN"
                ]
            )

            packaging_status = st.selectbox(
                "Packaging Status",
                [
                    "PACKED",
                    "UNPACKED"
                ]
            )

            pickup_address = st.text_area(
                "Pickup Address"
            )

            submitted = st.form_submit_button(
                "Create Food Donation"
            )

            if submitted:

                from datetime import datetime

                prepared_datetime = datetime.combine(
                    prepared_date,
                    prepared_time
                )

                expiry_datetime = datetime.combine(
                    expiry_date,
                    expiry_time
                )

                donation_data = {
                    "restaurant_id": restaurant_id,
                    "food_name": food_name,
                    "food_category": food_category,
                    "quantity": quantity,
                    "unit": unit,
                    "prepared_time": (
                        prepared_datetime.isoformat()
                    ),
                    "expiry_time": (
                        expiry_datetime.isoformat()
                    ),
                    "food_type": food_type,
                    "packaging_status": packaging_status,
                    "pickup_address": pickup_address
                }

                result = create_donation_from_api(
                    donation_data
                )

                if "error" in result:

                    st.error(
                        f"Error creating donation: "
                        f"{result['error']}"
                    )

                else:

                    flash_success(
                        f"Food donation created successfully! "
                        f"Donation ID: "
                        f"{result['donation_id']}"
                    )

    st.divider()

    st.subheader("Available Food Donations")

    try:

        donation_response = (
            get_available_donations_from_api()
        )

        if "error" in donation_response:

            st.error(
                donation_response["error"]
            )

            donations = []

        else:

            donations = donation_response["donations"]

        if donations:

            for donation in donations:

                st.write(
                    f"**{donation[2]}** — "
                    f"{donation[4]} {donation[5]} — "
                    f"{donation[1]} — "
                    f"Expires: {donation[7]}"
                )

        else:

            st.info(
                "No available food donations."
            )

    except Exception as e:

        st.error(
            f"Error loading donations: {e}"
        )


# =========================================================
# ORGANIZATIONS
# =========================================================

def organizations_page():

    st.header("🏢 Organization / NGO Management")

    st.subheader("Register Organization")

    with st.form("organization_form"):

        organization_name = st.text_input(
            "Organization Name"
        )

        contact_person = st.text_input(
            "Contact Person"
        )

        phone = st.text_input(
            "Phone"
        )

        email = st.text_input(
            "Email"
        )

        address = st.text_area(
            "Address"
        )

        city = st.text_input(
            "City"
        )

        organization_type = st.selectbox(
            "Organization Type",
            [
                "NGO",
                "Charity",
                "Food Bank",
                "Community Organization",
                "Other"
            ]
        )

        submitted = st.form_submit_button(
            "Register Organization"
        )

        if submitted:

            organization_data = {
                "organization_name": organization_name,
                "contact_person": contact_person,
                "phone": phone,
                "email": email,
                "address": address,
                "city": city,
                "organization_type": organization_type
            }

            result = create_organization_from_api(
                organization_data
            )

            if "error" in result:

                st.error(
                    f"Error registering organization: "
                    f"{result['error']}"
                )

            else:

                flash_success(
                    f"Organization registered successfully! "
                    f"Organization ID: "
                    f"{result['organization_id']}"
                )

    st.divider()

    st.subheader("Verified Organizations")

    organization_response = (
        get_verified_organizations_from_api()
    )

    if "error" in organization_response:

        st.error(
            organization_response["error"]
        )

    else:

        organizations = organization_response["organizations"]

        if organizations:

            for organization in organizations:

                st.write(
                    f"**{organization[1]}** — "
                    f"{organization[2]} — "
                    f"{organization[6]} — "
                    f"{organization[7]}"
                )

        else:

            st.info(
                "No verified organizations available."
            )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_page():

    st.header("👨‍💼 Admin Dashboard")

    # -----------------------------------------------------
    # VOLUNTEER SUMMARY
    # -----------------------------------------------------

    summary = get_volunteer_summary_from_api()

    if "error" in summary:

        st.error(summary["error"])

    else:

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "👥 Total Volunteers",
                summary["total_volunteers"]
            )

        with col2:

            st.metric(
                "✅ Active Volunteers",
                summary["active_volunteers"]
            )

        with col3:

            st.metric(
                "🟢 Available Volunteers",
                summary["available_volunteers"]
            )

        with col4:

            st.metric(
                "🚚 Busy Volunteers",
                summary["busy_volunteers"]
            )

    # -----------------------------------------------------
    # ORGANIZATION SUMMARY
    # -----------------------------------------------------

    organization_summary = (
        get_organization_summary_from_api()
    )

    if "error" in organization_summary:

        st.error(
            organization_summary["error"]
        )

    else:

        st.subheader("🏢 Organization Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "🏢 Total Organizations",
                organization_summary["total_organizations"]
            )

        with col2:

            st.metric(
                "✅ Verified",
                organization_summary["verified_organizations"]
            )

        with col3:

            st.metric(
                "⏳ Pending",
                organization_summary["pending_organizations"]
            )

        with col4:

            st.metric(
                "❌ Rejected",
                organization_summary["rejected_organizations"]
            )

    # -----------------------------------------------------
    # DONATION SUMMARY
    # -----------------------------------------------------

    donation_summary = get_donation_summary_from_api()

    if "error" in donation_summary:

        st.error(
            donation_summary["error"]
        )

    else:

        st.subheader("🍱 Donation Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "🍱 Total Donations",
                donation_summary["total_donations"]
            )

        with col2:

            st.metric(
                "🟢 Available",
                donation_summary["available_donations"]
            )

        with col3:

            st.metric(
                "🔒 Reserved",
                donation_summary["reserved_donations"]
            )

        with col4:

            st.metric(
                "🚚 Picked Up",
                donation_summary["picked_up_donations"]
            )

        with col5:

            st.metric(
                "✅ Delivered",
                donation_summary["delivered_donations"]
            )
        st.subheader("📊 Donation Status")

        donation_chart_data = {
            "Status": [
                "Available",
                "Reserved",
                "Picked Up",
                "Delivered"
            ],
            "Count": [
                donation_summary["available_donations"],
                donation_summary["reserved_donations"],
                donation_summary["picked_up_donations"],
                donation_summary["delivered_donations"]
            ]
        }

        st.bar_chart(
            donation_chart_data,
            x="Status",
            y="Count"
        )

    # -----------------------------------------------------
    # PICKUP SUMMARY
    # -----------------------------------------------------

    pickup_summary = get_pickup_summary_from_api()

    if "error" in pickup_summary:

        st.error(
            pickup_summary["error"]
        )

    else:

        st.subheader("🚚 Pickup Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "🚚 Total Pickups",
                pickup_summary["total_pickups"]
            )

        with col2:

            st.metric(
                "📋 Requested",
                pickup_summary["requested_pickups"]
            )

        with col3:

            st.metric(
                "🤝 Accepted",
                pickup_summary["accepted_pickups"]
            )

        with col4:

            st.metric(
                "📦 Picked Up",
                pickup_summary["picked_up_pickups"]
            )

        with col5:

            st.metric(
                "✅ Delivered",
                pickup_summary["delivered_pickups"]
            )
        st.subheader("📊 Pickup Status")

        pickup_chart_data = {
            "Status": [
                "Requested",
                "Accepted",
                "Picked Up",
                "Delivered"
            ],
            "Count": [
                pickup_summary["requested_pickups"],
                pickup_summary["accepted_pickups"],
                pickup_summary["picked_up_pickups"],
                pickup_summary["delivered_pickups"]
            ]
        }

        st.bar_chart(
            pickup_chart_data,
            x="Status",
            y="Count"
        )

    # =====================================================
    # AI FOOD RISK ANALYSIS
    # =====================================================

    st.subheader("🤖 AI Food Risk Analysis")

    risk_response = get_food_risk_analysis_from_api()

    if "error" in risk_response:

        st.error(
            risk_response["error"]
        )

    else:

        risk_results = risk_response.get(
            "risk_analysis",
            []
        )

        if not risk_results:

            st.success(
                "No active donations require risk analysis. ✅"
            )

        else:

            # -------------------------------------------------
            # AI RISK SUMMARY
            # -------------------------------------------------

            high_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "HIGH"
            )

            medium_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "MEDIUM"
            )

            low_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "LOW"
            )

            expired_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "EXPIRED"
            )

            st.markdown(
                "### 📊 AI Risk Summary"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "🔴 High Risk",
                    high_count
                )

            with col2:

                st.metric(
                    "🟠 Medium Risk",
                    medium_count
                )

            with col3:

                st.metric(
                    "🟢 Low Risk",
                    low_count
                )

            with col4:

                st.metric(
                    "⚫ Expired",
                    expired_count
                )
            st.subheader("📊 Food Risk Distribution")

            risk_chart_data = {
                "Risk Level": [
                    "HIGH",
                    "MEDIUM",
                    "LOW",
                    "EXPIRED"
                ],
                "Count": [
                    high_count,
                    medium_count,
                    low_count, 
                    expired_count
                ]
            }

            st.bar_chart(
                risk_chart_data,
                x="Risk Level",
                y="Count"
            )

            # -------------------------------------------------
            # INDIVIDUAL RISK ANALYSIS
            # -------------------------------------------------

            st.markdown(
                "### 🔍 Donation Risk Details"
            )

            risk_priority = {
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
                "EXPIRED": 4
            }

            risk_results = sorted(
                risk_results,
                key=lambda risk: (
                    risk_priority.get(
                        risk["risk_level"],
                        99
                    ),
                    risk["hours_remaining"]
                )
            )

            for risk in risk_results:

                st.markdown("---")

                st.write(
                    f"### 🍱 {risk['food_name']}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write(
                        f"**Donation ID:** "
                        f"{risk['donation_id']}"
                    )

                with col2:

                    st.write(
                        f"**Quantity:** "
                        f"{risk['quantity']} "
                        f"{risk['unit']}"
                    )

                with col3:

                    st.write(
                        f"**Risk:** "
                        f"{risk['risk_level']}"
                    )

                with col4:

                    st.write(
                        f"**Score:** "
                        f"{risk['risk_score']}"
                    )

                st.write(
                    f"**Priority:** "
                    f"{risk['priority']}"
                )

                st.info(
                    f"**🤖 Recommended Action:** "
                    f"{risk['recommended_action']}"
                )

                st.write(
                    f"**Hours Remaining:** "
                    f"{risk['hours_remaining']}"
                )

                st.write("**Reasons:**")

                for reason in risk["reasons"]:

                    st.write(
                        f"- {reason}"
                    )

    # -----------------------------------------------------
    # PENDING ORGANIZATIONS
    # -----------------------------------------------------

    st.divider()

    st.subheader("Pending Organizations")

    try:

        organization_response = (
            get_pending_organizations_from_api()
        )

        if "error" in organization_response:

            st.error(
                organization_response["error"]
            )

            organizations = []

        else:

            organizations = (
                organization_response["organizations"]
            )

        if organizations:

            for organization in organizations:

                organization_id = organization[0]
                organization_name = organization[1]
                contact_person = organization[2]
                phone = organization[3]
                email = organization[4]
                address = organization[5]
                city = organization[6]
                organization_type = organization[7]
                verification_status = organization[8]
                status = organization[9]

                st.markdown("---")

                st.subheader(
                    f"🏢 {organization_name}"
                )

                st.write(
                    f"**Organization ID:** "
                    f"{organization_id}"
                )

                st.write(
                    f"**Contact Person:** "
                    f"{contact_person}"
                )

                st.write(
                    f"**Phone:** {phone}"
                )

                st.write(
                    f"**Email:** {email}"
                )

                st.write(
                    f"**Address:** {address}"
                )

                st.write(
                    f"**City:** {city}"
                )

                st.write(
                    f"**Organization Type:** "
                    f"{organization_type}"
                )

                st.write(
                    f"**Verification Status:** "
                    f"{verification_status}"
                )

                st.write(
                    f"**Status:** {status}"
                )

                st.write(
                    "### Admin Decision"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "✅ Verify Organization",
                        key=f"verify_{organization_id}"
                    ):

                        result = (
                            verify_organization_from_api(
                                organization_id
                            )
                        )

                        if "error" in result:

                            st.error(
                                f"Error verifying organization: "
                                f"{result['error']}"
                            )

                        else:

                            flash_success(
                                f"Organization "
                                f"#{result['organization_id']} "
                                f"verified successfully!"
                            )

                with col2:

                    rejection_reason = st.text_input(
                        "Rejection Reason",
                        key=f"reason_{organization_id}",
                        placeholder="Enter reason for rejection"
                    )

                    if st.button(
                        "❌ Reject Organization",
                        key=f"reject_{organization_id}"
                    ):

                        if not rejection_reason.strip():

                            st.warning(
                                "Please enter a rejection reason."
                            )

                        else:

                            result = (
                                reject_organization_from_api(
                                    organization_id,
                                    rejection_reason
                                )
                            )

                            if "error" in result:

                                st.error(
                                    f"Error rejecting organization: "
                                    f"{result['error']}"
                                )

                            else:

                                flash_success(
                                    f"Organization "
                                    f"#{result['organization_id']} "
                                    f"has been rejected successfully!"
                                )

        else:

            st.success(
                "No organizations are waiting "
                "for verification. ✅"
            )

    except Exception as e:

        st.error(
            f"Error loading pending organizations: {e}"
        )

    # -----------------------------------------------------
    # VOLUNTEER MANAGEMENT
    # -----------------------------------------------------

    st.divider()

    st.subheader("🚗 Volunteer Management")

    st.write("### Add Volunteer")

    with st.form("volunteer_form"):

        volunteer_name = st.text_input(
            "Volunteer Name"
        )

        phone = st.text_input(
            "Phone"
        )

        email = st.text_input(
            "Email"
        )

        address = st.text_area(
            "Address"
        )

        city = st.text_input(
            "City"
        )

        submitted = st.form_submit_button(
            "Add Volunteer"
        )

        if submitted:

            if not volunteer_name.strip():

                st.error(
                    "Volunteer name is required."
                )

            elif not phone.strip():

                st.error(
                    "Phone number is required."
                )

            elif not city.strip():

                st.error(
                    "City is required."
                )

            else:

                volunteer_data = {
                    "volunteer_name": volunteer_name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "city": city
                }

                result = create_volunteer_from_api(
                    volunteer_data
                )

                if "error" in result:

                    st.error(
                        f"Error creating volunteer: "
                        f"{result['error']}"
                    )

                else:

                    flash_success(
                        f"Volunteer created successfully! "
                        f"Volunteer ID: "
                        f"{result['volunteer_id']}"
                    )

    st.divider()

    st.write("### Registered Volunteers")

    volunteer_response = get_volunteers_from_api()

    if "error" in volunteer_response:

        st.error(
            volunteer_response["error"]
        )

    else:

        volunteers = volunteer_response["volunteers"]

        if volunteers:

            for volunteer in volunteers:

                st.write(
                    f"**{volunteer[1]}** — "
                    f"{volunteer[2]} — "
                    f"{volunteer[5]} — "
                    f"Availability: {volunteer[6]} — "
                    f"Status: {volunteer[7]}"
                )

        else:

            st.info(
                "No volunteers registered yet."
            )


# =========================================================
# PICKUP REQUESTS
# =========================================================

def pickups_page():

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


# =========================================================
# MENU (each role sees only its own pages: see app/navigation.py)
# =========================================================

PAGE_FUNCTIONS = {
    "home": home_page,
    "my-restaurant": my_restaurant_page,
    "my-organization": my_organization_page,
    "available-food": available_food_page,
    "donations": donations_page,
    "pickups": pickups_page,
    "restaurants": restaurants_page,
    "organizations": organizations_page,
    "admin": admin_page,
    "user-access": user_access_page,
}


def only_for_this_role(path, page_function):
    """Extra safety: never draw a page that is not in this role's menu."""
    def guarded_page():
        if path not in pages_for(role):
            st.error("You do not have access to this page.")
            st.stop()
        page_function()

    return guarded_page


def build_menu():
    return {
        section: [
            st.Page(
                only_for_this_role(path, PAGE_FUNCTIONS[path]),
                title=title_for(role, path),
                icon=PAGES[path][1],
                url_path=path,
                default=(path == "home"),
            )
            for path in paths
        ]
        for section, paths in MENU[role].items()
    }


current_page = st.navigation(build_menu(), position="sidebar")

st.sidebar.divider()
st.sidebar.markdown(
    f"**{user['full_name'] or user['email']}**  \n"
    f"{ROLE_LABELS[role]}"
)
logout_button()
st.sidebar.caption(privacy_link_markdown())

current_page.run()
