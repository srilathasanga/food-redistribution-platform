"""Kitchens: My restaurant (donor) and Restaurants (admin)."""

import streamlit as st

from app import ui
from app.backend import (
    create_restaurant_from_api,
    get_restaurants_from_api,
    link_restaurant,
)


def contact_problems(phone, email):
    """Friendly 'what to fix' messages for an optional phone and email."""
    problems = []
    digits = "".join(ch for ch in phone if ch.isdigit())
    if phone.strip() and not 10 <= len(digits) <= 13:
        problems.append("Please enter the phone as a 10-digit mobile number.")
    if email.strip() and "@" not in email:
        problems.append("Please check the email address.")
    return problems


def _kitchen_form(form_key, submit_label, defaults=None):
    """The add-a-kitchen form. Returns the checked details, or None."""
    defaults = defaults or {}
    with st.form(form_key):
        col1, col2 = st.columns(2)
        name = col1.text_input("Restaurant or kitchen name",
                               placeholder="e.g. Grace Kitchen")
        contact_person = col2.text_input(
            "Contact person", value=defaults.get("contact_person", ""),
            placeholder="e.g. Anil Kumar",
        )
        col1, col2 = st.columns(2)
        phone = col1.text_input(
            "Phone", value=defaults.get("phone", ""),
            placeholder="10-digit mobile",
            help="Volunteers call this number when they arrive.",
        )
        email = col2.text_input(
            "Email (optional)", value=defaults.get("email", ""),
            placeholder="e.g. kitchen@example.com",
        )
        address = st.text_area("Address", height=90,
                               placeholder="Street, area and landmark")
        city = st.text_input("City", value=defaults.get("city", ""),
                             placeholder="e.g. Hyderabad")
        if not st.form_submit_button(submit_label, type="primary",
                                     icon=":material/add:", width="stretch"):
            return None

        problems = ([] if name.strip() else
                    ["Please enter the restaurant or kitchen name."])
        problems += contact_problems(phone, email)
        for problem in problems:
            st.error(problem, icon=":material/error:")
        if problems:
            return None
        return {
            "restaurant_name": name.strip(),
            "contact_person": contact_person.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "address": address.strip(),
            "city": city.strip(),
        }


def _kitchen_lines(contact_person, phone, email, address, city):
    lines = []
    place = ", ".join(part for part in (address, city) if part)
    if place:
        lines.append(f":material/location_on: {place}")
    if contact_person:
        lines.append(f":material/person: {contact_person}")
    if phone:
        lines.append(f":material/call: [{phone}](tel:{phone})")
    if email:
        lines.append(f":material/mail: [{email}](mailto:{email})")
    return "  \n".join(lines) or "No details yet."


# ---------------------------------------------------------------- donor

def my_restaurant_page(ctx):
    ui.page_header("My restaurant",
                   "The kitchen you share food from.",
                   icon=":material/storefront:")

    restaurant = ctx.my_restaurant
    if restaurant:
        (_, name, contact_person, phone, email, address, city,
         status) = restaurant[:8]
        with ui.card():
            ui.person_header(name, [city])
            st.markdown(ui.badge_markdown(status or "ACTIVE"))
            st.markdown(_kitchen_lines(contact_person, phone, email,
                                       address, city))
        st.caption("To change these details, please contact the ministry "
                   "admin.")
        if st.button("Share surplus food", type="primary",
                     icon=":material/add_circle:", width="stretch"):
            st.switch_page(ctx.pages["donations"])
        return

    st.markdown("Add the restaurant or kitchen you share food from. "
                "You only do this once.")
    user = ctx.user
    details = _kitchen_form("my_restaurant_form", "Save my kitchen", {
        "contact_person": user["full_name"] or "",
        "phone": user["phone"] or "",
        "email": user["email"],
        "city": user["city"] or "",
    })
    if details:
        result = create_restaurant_from_api(details)
        if "error" in result:
            st.error(f"Could not save your kitchen: {result['error']}",
                     icon=":material/error:")
        else:
            link_restaurant(user["email"], result["restaurant_id"])
            ui.flash_success(
                f"{details['restaurant_name']} is saved. Next: tap "
                "\"Share surplus food\" whenever you have food to give."
            )


# ---------------------------------------------------------------- admin

def restaurants_page(ctx):
    ui.page_header(
        "Restaurants",
        "Kitchens and restaurants that share their surplus food.",
        icon=":material/storefront:",
    )

    restaurants = ui.rows(get_restaurants_from_api(), "restaurants")

    with st.expander("Add a restaurant or kitchen",
                     icon=":material/add_business:",
                     expanded=(ui.form_requested("restaurant")
                               or not restaurants)):
        details = _kitchen_form("restaurant_form", "Add restaurant")
        if details:
            result = create_restaurant_from_api(details)
            if "error" in result:
                st.error(f"Could not add the restaurant: {result['error']}",
                         icon=":material/error:")
            else:
                ui.flash_success(
                    f"{details['restaurant_name']} was added. Next: share "
                    "food for it under Food donations."
                )

    if not restaurants:
        ui.empty_state(
            "No restaurants yet. Add the first one to start sharing food!",
            icon=":material/storefront:", image="empty-food",
            hint="Use the form above. Donors can also add their own "
                 "kitchen when they sign in.",
        )
        return

    ui.section_title(ui.plural(len(restaurants), "restaurant"),
                     ":material/storefront:", "blue")
    for column, restaurant in ui.grid(restaurants):
        (_, name, contact_person, phone, email, address, city, status,
         _created) = restaurant
        with column, ui.card():
            ui.person_header(name, [city])
            st.markdown(ui.badge_markdown(status or "ACTIVE"))
            st.markdown(_kitchen_lines(contact_person, phone, email,
                                       address, city))
