"""Food: Food donations / My donations, and Available food."""

from datetime import timedelta

import streamlit as st

from app import ui
from app.backend import (
    create_donation_from_api,
    get_available_donations_from_api,
    get_my_donations_from_api,
    get_requestable_donations_from_api,
    get_restaurants_from_api,
)
from app.home_pages import organization_is_verified, requestable_food
from app.timeutil import now_local

CATEGORIES = ["Cooked meals", "Rice and curries", "Bread and bakery",
              "Fruit and vegetables", "Packaged food", "Sweets and snacks",
              "Other"]
UNITS = ["kg", "plates", "packets", "boxes", "pieces", "loaves", "litres"]
FOOD_TYPES = {"VEGETARIAN": "Vegetarian", "NON_VEGETARIAN": "Non-vegetarian"}
PACKAGING = {"PACKED": "Packed", "UNPACKED": "Not packed"}

# Simple choices instead of date and time pickers (easier on a phone).
COOKED_HOURS_AGO = {"Just now": 0, "About 1 hour ago": 1,
                    "About 2 hours ago": 2, "About 3 hours ago": 3,
                    "4 or more hours ago": 4}
SAFE_FOR_HOURS = {"1 hour": 1, "2 hours": 2, "3 hours": 3, "4 hours": 4,
                  "6 hours": 6, "8 hours": 8, "12 hours": 12,
                  "24 hours": 24}


def _urgency(expiry_time, now):
    """'HIGH' (under 2 hours), 'MEDIUM' (under 6) or None."""
    hours = (ui.to_datetime(expiry_time) - now).total_seconds() / 3600
    return "HIGH" if hours < 2 else "MEDIUM" if hours <= 6 else None


# ---------------------------------------------------------------- share food

def _share_food_form(restaurant):
    """The form for one restaurant. Returns the donation details, or None."""
    restaurant_id, name = restaurant[0], restaurant[1]
    default_address = ", ".join(part for part in (restaurant[5],
                                                  restaurant[6]) if part)
    with st.form(f"donation_form_{restaurant_id}"):
        col1, col2 = st.columns(2)
        food_name = col1.text_input("What food is it?",
                                    placeholder="e.g. Vegetable biryani")
        category = col2.selectbox("Kind of food", CATEGORIES)
        col1, col2 = st.columns(2)
        quantity = col1.number_input("How much?", min_value=0.5, step=0.5,
                                     value=None, placeholder="e.g. 20")
        unit = col2.selectbox("Unit", UNITS)
        col1, col2 = st.columns(2)
        cooked = col1.selectbox("When was it cooked?",
                                list(COOKED_HOURS_AGO))
        safe_for = col2.selectbox(
            "Safe to eat for about", list(SAFE_FOR_HOURS), index=1,
            help="From now. After this time the food is no longer offered.",
        )
        col1, col2 = st.columns(2)
        food_type = col1.radio("Vegetarian?", list(FOOD_TYPES),
                               format_func=FOOD_TYPES.get, horizontal=True)
        packaging = col2.radio("Packed?", list(PACKAGING),
                               format_func=PACKAGING.get, horizontal=True)
        pickup_address = st.text_area(
            "Where should the volunteer collect it?", value=default_address,
            height=80, placeholder="Street, area and landmark",
        )
        if not st.form_submit_button("Share this food", type="primary",
                                     icon=":material/volunteer_activism:",
                                     width="stretch"):
            return None

    problems = []
    if not food_name.strip():
        problems.append("Please say what the food is.")
    if not quantity:
        problems.append("Please enter how much food there is.")
    if not pickup_address.strip():
        problems.append("Please add the pickup address so the volunteer "
                        "can find it.")
    for problem in problems:
        st.error(problem, icon=":material/error:")
    if problems:
        return None

    now = now_local().replace(second=0, microsecond=0)
    return {
        "restaurant_id": restaurant_id,
        "restaurant_name": name,
        "food_name": food_name.strip(),
        "food_category": category,
        "quantity": quantity,
        "unit": unit,
        "prepared_time": (now - timedelta(hours=COOKED_HOURS_AGO[cooked])
                          ).isoformat(),
        "expiry_time": (now + timedelta(hours=SAFE_FOR_HOURS[safe_for])
                        ).isoformat(),
        "safe_for": safe_for,
        "food_type": food_type,
        "packaging_status": packaging,
        "pickup_address": pickup_address.strip(),
    }


def _share_food(restaurants):
    if len(restaurants) == 1:
        restaurant = restaurants[0]
        st.markdown(f":material/storefront: Sharing from **{restaurant[1]}**")
    else:
        index = st.selectbox("Which restaurant or kitchen?",
                             range(len(restaurants)),
                             format_func=lambda i: restaurants[i][1])
        restaurant = restaurants[index]
    details = _share_food_form(restaurant)
    if not details:
        return
    result = create_donation_from_api(details)
    if "error" in result:
        st.error(f"Could not share the food: {result['error']}",
                 icon=":material/error:")
    else:
        ui.flash_success(
            f"Thank you! {details['food_name']} is now offered for "
            f"{details['safe_for']}. Next: an organization requests it and "
            "a coordinator sends a volunteer."
        )


# ---------------------------------------------------------------- pages

def donations_page(ctx):
    now = now_local()
    if ctx.is_admin:
        ui.page_header("Food donations",
                       "Share food for any kitchen, and see what is "
                       "waiting to be collected.",
                       icon=":material/soup_kitchen:")
        restaurants = ui.rows(get_restaurants_from_api(), "restaurants")
    else:
        ui.page_header("My donations",
                       "Share surplus food and see what happened to it.",
                       icon=":material/soup_kitchen:")
        restaurants = [ctx.my_restaurant] if ctx.my_restaurant else []

    if not restaurants:
        ui.empty_state(
            "First, add the kitchen you share food from",
            icon=":material/storefront:", image="signin",
            hint="You only do this once.",
            button_label="Add a kitchen",
            page=ctx.pages["restaurants" if ctx.is_admin
                           else "my-restaurant"],
        )
        return

    # (Always open; Home's "Share food" quick action lands here.)
    with st.expander("Share surplus food", icon=":material/add_circle:",
                     expanded=True):
        _share_food(restaurants)

    if ctx.is_admin:
        _all_available_food(now)
    else:
        _my_donations(ctx.my_restaurant[0], now)


def _my_donations(restaurant_id, now):
    ui.section_title("My recent donations", ":material/soup_kitchen:",
                     "green")
    donations = ui.rows(get_my_donations_from_api(restaurant_id, 20),
                        "donations")
    if not donations:
        ui.empty_state(
            "You haven't shared any food yet",
            icon=":material/soup_kitchen:", image="empty-food",
            hint="When you share food, you'll see here when it is "
                 "requested, picked up and delivered.",
        )
        return
    for column, donation in ui.grid(donations):
        (_, food_name, quantity, unit, expiry_time, status, created) = donation
        expired = (status == "AVAILABLE"
                   and ui.to_datetime(expiry_time) <= now)
        with column, ui.card():
            ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                          ":material/soup_kitchen:", "green")
            st.markdown(ui.badge_markdown("EXPIRED" if expired else status))
            st.caption(
                f"Shared {ui.friendly_time(created, now)} · "
                + ("expired" if expired else
                   f"expires {ui.friendly_time(expiry_time, now)}"
                   if status in ("AVAILABLE", "RESERVED") else
                   f"best before {ui.clock_time(expiry_time)}")
            )


def _all_available_food(now):
    food = ui.rows(get_available_donations_from_api(), "donations")
    requestable = {row[0] for row in
                   ui.rows(get_requestable_donations_from_api(), "donations")}
    ui.section_title(ui.plural(len(food), "item") + " of food available now",
                     ":material/restaurant:", "green")
    if not food:
        ui.empty_state("No food is waiting right now",
                       icon=":material/restaurant:", image="empty-food",
                       hint="Shared food appears here until it is "
                            "collected or expires.")
        return
    for column, donation in ui.grid(food):
        (donation_id, restaurant, food_name, _category, quantity, unit,
         _prepared, expiry_time, food_type, _packaging, address,
         status) = donation
        urgency = _urgency(expiry_time, now)
        badges = [ui.badge_markdown(status if donation_id in requestable
                                    else "REQUESTED")]
        if urgency:
            badges.append(ui.badge_markdown(urgency))
        with column, ui.card():
            ui.card_title(f"{food_name} · {ui.amount(quantity, unit)}",
                          ":material/restaurant:", "green")
            st.markdown(f":gray-badge[{FOOD_TYPES.get(food_type, food_type)}]")
            st.markdown(" ".join(badges))
            st.markdown(
                f":material/storefront: {restaurant}"
                + (f"  \n:material/location_on: {address}" if address else "")
                + f"  \n:material/schedule: Expires "
                f"**{ui.friendly_time(expiry_time, now)}**"
            )


def available_food_page(ctx):
    ui.page_header("Available food",
                   "Good food you can request for the people you serve.",
                   icon=":material/restaurant:")
    if not ctx.my_organization:
        ui.empty_state(
            "First, tell us about your organization",
            icon=":material/apartment:", image="empty-people",
            hint="A coordinator checks every organization before it can "
                 "request food.",
            button_label="Add my organization",
            page=ctx.pages["my-organization"],
        )
        return
    if organization_is_verified(ctx.my_organization):
        requestable_food(ctx.my_organization, now_local(), ui.flash_success)
