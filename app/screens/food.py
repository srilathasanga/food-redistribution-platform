"""Food: Food donations / My donations, and Available food."""

import streamlit as st

from app import ui
from app.backend import (
    create_donation_from_api,
    get_available_donations_from_api,
    get_restaurants_from_api,
)
from app.timeutil import now_local

flash_success = ui.flash_success


def donations_page(ctx):
    user = ctx.user
    is_admin = ctx.is_admin

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


def available_food_page(ctx):

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
