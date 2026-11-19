"""Kitchens: My restaurant (donor) and Restaurants (admin)."""

import streamlit as st

from app import ui
from app.backend import (
    create_restaurant_from_api,
    get_restaurants_from_api,
)
from app.user_service import (
    link_restaurant,
)

flash_success = ui.flash_success


def my_restaurant_page(ctx):
    user = ctx.user
    my_restaurant = ctx.my_restaurant

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


def restaurants_page(ctx):

    ui.page_header(
        "Restaurants",
        "Kitchens and restaurants that share their surplus food.",
        icon=":material/storefront:",
    )

    restaurant_response = get_restaurants_from_api()
    if "error" in restaurant_response:
        st.error(restaurant_response["error"], icon=":material/error:")
        restaurants = []
    else:
        restaurants = restaurant_response["restaurants"]

    # ---- Add a restaurant (open straight away when the list is empty)
    with st.expander("Add a restaurant or kitchen",
                     icon=":material/add_business:",
                     expanded=not restaurants):
        with st.form("restaurant_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            restaurant_name = col1.text_input(
                "Restaurant or kitchen name",
                placeholder="e.g. Grace Kitchen",
            )
            contact_person = col2.text_input(
                "Contact person", placeholder="e.g. Anil Kumar",
            )
            col1, col2 = st.columns(2)
            phone = col1.text_input(
                "Phone", placeholder="10-digit mobile",
                help="Volunteers call this number when they arrive.",
            )
            email = col2.text_input(
                "Email (optional)", placeholder="e.g. kitchen@example.com",
            )
            address = st.text_area(
                "Address", placeholder="Street, area and landmark",
                height=90,
            )
            city = st.text_input("City", placeholder="e.g. Hyderabad")

            if st.form_submit_button("Add restaurant", type="primary",
                                     icon=":material/add:",
                                     width="stretch"):
                problems = []
                if not restaurant_name.strip():
                    problems.append("Please enter the restaurant or "
                                    "kitchen name.")
                digits = "".join(ch for ch in phone if ch.isdigit())
                if phone.strip() and not 10 <= len(digits) <= 13:
                    problems.append("Please enter the phone as a 10-digit "
                                    "mobile number.")
                if email.strip() and "@" not in email:
                    problems.append("Please check the email address.")
                for problem in problems:
                    st.error(problem, icon=":material/error:")

                if not problems:
                    result = create_restaurant_from_api({
                        "restaurant_name": restaurant_name.strip(),
                        "contact_person": contact_person.strip(),
                        "phone": phone.strip(),
                        "email": email.strip(),
                        "address": address.strip(),
                        "city": city.strip(),
                    })
                    if "error" in result:
                        st.error(f"Could not add the restaurant: "
                                 f"{result['error']}",
                                 icon=":material/error:")
                    else:
                        flash_success(
                            f"{restaurant_name.strip()} was added. Next: "
                            "share food for it under Food donations."
                        )

    # ---- The list, as cards
    if not restaurants:
        ui.empty_state(
            "No restaurants yet. Add the first one to start sharing food!",
            icon=":material/storefront:",
            hint="Use the form above. Donors can also add their own "
                 "kitchen when they sign in.",
        )
        return

    st.subheader(f"{len(restaurants)} "
                 + ("restaurant" if len(restaurants) == 1 else "restaurants"))
    for column, restaurant in ui.grid(restaurants):
        (_, name, contact_person, phone, email, address, city, status,
         _created) = restaurant
        with column, ui.card():
            st.markdown(f"#### {name}")
            st.markdown(ui.badge_markdown(status or "ACTIVE"))
            lines = []
            if city or address:
                place = ", ".join(part for part in (address, city) if part)
                lines.append(f":material/location_on: {place}")
            if contact_person:
                lines.append(f":material/person: {contact_person}")
            if phone:
                lines.append(f":material/call: [{phone}](tel:{phone})")
            if email:
                lines.append(f":material/mail: [{email}](mailto:{email})")
            st.markdown("  \n".join(lines) or "No details yet.")
