
import streamlit as st
import requests


FASTAPI_URL = "https://food-redistribution-platform-ya7e.onrender.com"


# =========================================================
# AVAILABLE DONATIONS API
# =========================================================

def get_available_donations_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/donations/available",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"API error: {response.status_code}"
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": (
                "FastAPI is not running. "
                "Please start FastAPI on port 8000."
            )
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# DONATION SUMMARY API
# =========================================================

def get_donation_summary_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/donations/summary",
            timeout=5
        )

        if response.status_code == 200:

            return response.json()["summary"]

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# PICKUP REQUESTS API
# =========================================================

def get_pickup_requests_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/pickups",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"API error: {response.status_code}"
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# RESTAURANTS API
# =========================================================

def get_restaurants_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/restaurants",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"API error: {response.status_code}"
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# VOLUNTEER API
# =========================================================

def create_volunteer_from_api(volunteer_data):

    try:

        response = requests.post(
            f"{FASTAPI_URL}/volunteers",
            json=volunteer_data,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


def get_volunteers_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/volunteers",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# VOLUNTEER SUMMARY API
# =========================================================

def get_volunteer_summary_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/volunteers/summary",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()["summary"]

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# PICKUP SUMMARY API
# =========================================================

def get_pickup_summary_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/pickups/summary",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()["summary"]

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# RESTAURANT CREATE API
# =========================================================

def create_restaurant_from_api(restaurant_data):

    try:

        response = requests.post(
            f"{FASTAPI_URL}/restaurants",
            json=restaurant_data,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# DONATION CREATE API
# =========================================================

def create_donation_from_api(donation_data):

    try:

        response = requests.post(
            f"{FASTAPI_URL}/donations",
            json=donation_data,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# ORGANIZATION API
# =========================================================

def create_organization_from_api(organization_data):

    try:

        response = requests.post(
            f"{FASTAPI_URL}/organizations",
            json=organization_data,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


def get_verified_organizations_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/organizations/verified",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"API error: {response.status_code}"
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


def get_pending_organizations_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/organizations/pending",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"API error: {response.status_code}"
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# ORGANIZATION SUMMARY API
# =========================================================

def get_organization_summary_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/organizations/summary",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()["summary"]

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# VERIFY ORGANIZATION API
# =========================================================

def verify_organization_from_api(organization_id):

    try:

        response = requests.put(
            f"{FASTAPI_URL}/organizations/{organization_id}/verify",
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# REJECT ORGANIZATION API
# =========================================================

def reject_organization_from_api(
    organization_id,
    rejection_reason
):

    try:

        response = requests.put(
            f"{FASTAPI_URL}/organizations/{organization_id}/reject",
            json={
                "rejection_reason": rejection_reason
            },
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# PICKUP CREATE API
# =========================================================

def create_pickup_from_api(pickup_data):

    try:

        response = requests.post(
            f"{FASTAPI_URL}/pickups",
            json=pickup_data,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# UPDATE PICKUP STATUS API
# =========================================================

def update_pickup_status_from_api(
    pickup_id,
    new_status
):

    try:

        response = requests.put(
            f"{FASTAPI_URL}/pickups/{pickup_id}/status",
            json={
                "new_status": new_status
            },
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# ASSIGN VOLUNTEER API
# =========================================================

def assign_volunteer_to_pickup_from_api(
    pickup_id,
    volunteer_id
):

    try:

        response = requests.put(
            f"{FASTAPI_URL}/pickups/{pickup_id}/volunteer",
            json={
                "volunteer_id": volunteer_id
            },
            timeout=5
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# AI FOOD RISK ANALYSIS API
# =========================================================

def get_food_risk_analysis_from_api():

    try:

        response = requests.get(
            f"{FASTAPI_URL}/donations/risk-analysis",
            timeout=5
        )

        if response.status_code == 200:

            return response.json()

        return {
            "error": response.json().get(
                "detail",
                f"API error: {response.status_code}"
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "error": "FastAPI is not running."
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": f"Request failed: {str(e)}"
        }


# =========================================================
# STREAMLIT PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Food Redistribution Platform",
    page_icon="🍲",
    layout="wide"
)


st.title("🍲 Food Redistribution Platform")

st.write(
    "Connecting surplus food from restaurants "
    "with verified organizations for redistribution."
)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Choose a module",
    [
        "Home",
        "Restaurants",
        "Food Donations",
        "Organizations",
        "Admin",
        "Pickup Requests"
    ]
)


# =========================================================
# HOME
# =========================================================

if menu == "Home":

    st.header("Welcome")

    st.success(
        "Food Redistribution Platform is running successfully! ✅"
    )

    st.info(
        "Backend: Python + PostgreSQL\n\n"
        "Frontend: Streamlit"
    )


# =========================================================
# RESTAURANTS
# =========================================================

elif menu == "Restaurants":

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

                    st.success(
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

elif menu == "Food Donations":

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

    if not restaurants:

        st.warning(
            "No restaurants are available. "
            "Please register a restaurant first."
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
                "Prepared Date"
            )

            prepared_time = st.time_input(
                "Prepared Time"
            )

            expiry_date = st.date_input(
                "Expiry Date"
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

                    st.success(
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

elif menu == "Organizations":

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

                st.success(
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

elif menu == "Admin":

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

                            st.success(
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

                                st.success(
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

                    st.success(
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

elif menu == "Pickup Requests":

    st.header("🚚 Pickup Requests")

    # -----------------------------------------------------
    # PICKUP REQUEST DASHBOARD
    # -----------------------------------------------------

    st.subheader("📋 Pickup Request Dashboard")

    try:

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

        volunteer_response = get_volunteers_from_api()

        if "error" in volunteer_response:

            st.error(
                volunteer_response["error"]
            )

            volunteers = []

        else:

            volunteers = (
                volunteer_response["volunteers"]
            )

        if not pickup_requests:

            st.info(
                "No pickup requests found."
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
                        f"{requested_at}"
                    )

                    st.write(
                        f"**Pickup Time:** "
                        f"{pickup_time}"
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

                                    st.success(
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

                    if pickup_status == "REQUESTED":

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

                                st.success(
                                    f"Pickup "
                                    f"#{result['pickup_id']} "
                                    f"accepted successfully!"
                                )

                    # -------------------------------------
                    # ACCEPTED → PICKED_UP
                    # -------------------------------------

                    elif pickup_status == "ACCEPTED":

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

                                st.success(
                                    f"Pickup "
                                    f"#{result['pickup_id']} "
                                    f"marked as PICKED_UP!"
                                )

                    # -------------------------------------
                    # PICKED_UP → DELIVERED
                    # -------------------------------------

                    elif pickup_status == "PICKED_UP":

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

                                st.success(
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
            f"{row[0]} - {row[1]} "
            f"({row[2]} {row[3]}) - {row[5]}":
            row[0]
            for row in available_donations
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

        if not verified_organizations:

            st.warning(
                "No verified organizations available."
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
                "Pickup Date"
            )

            pickup_time_input = st.time_input(
                "Pickup Time"
            )

            pickup_address = st.text_input(
                "Pickup Address"
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

                        st.success(
                            f"Pickup request created successfully! "
                            f"Pickup ID: {result['pickup_id']}"
                        )

                except Exception as e:

                    st.error(
                        str(e)
                    )

