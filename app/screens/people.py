"""People: Volunteers and User access (admin only)."""

import streamlit as st

from app import ui
from app.backend import (
    approve_user,
    create_volunteer_from_api,
    get_volunteers_from_api,
    list_users,
    set_user_status,
)
from app.screens.kitchens import contact_problems
from app.timeutil import now_local
from app.user_service import ROLES

ROLE_WORDS = {"ADMIN": "Admin", "DONOR": "Donor",
              "ORGANIZATION": "Organization", "VOLUNTEER": "Volunteer"}


# ---------------------------------------------------------------- volunteers

def volunteers_page(ctx):
    volunteers = ui.rows(get_volunteers_from_api(), "volunteers")
    free = [v for v in volunteers
            if v[6] == "AVAILABLE" and v[7] == "ACTIVE"]
    ui.page_header(
        "Volunteers",
        f"The people who collect and deliver food. "
        f"{ui.plural(len(free), 'volunteer')} free right now.",
        icon=":material/directions_walk:",
    )
    st.caption("People who sign up as volunteers get a volunteer profile "
               "automatically when you approve them under User access.")

    with st.expander("Add a volunteer", icon=":material/person_add:",
                     expanded=(ui.form_requested("volunteer")
                               or not volunteers)):
        with st.form("volunteer_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name", placeholder="e.g. Ravi Teja")
            phone = col2.text_input(
                "Phone", placeholder="10-digit mobile",
                help="Coordinators call this number about pickups.",
            )
            col1, col2 = st.columns(2)
            email = col1.text_input("Email (optional)",
                                    placeholder="e.g. ravi@example.com")
            city = col2.text_input("City", placeholder="e.g. Hyderabad")
            address = st.text_area("Area or address (optional)", height=80,
                                   placeholder="Helps choose nearby pickups")
            submitted = st.form_submit_button("Add volunteer",
                                              type="primary",
                                              icon=":material/add:",
                                              width="stretch")
        if submitted:
            problems = []
            if not name.strip():
                problems.append("Please enter the volunteer's name.")
            if not phone.strip():
                problems.append("Please enter a phone number, so "
                                "coordinators can reach them.")
            if not city.strip():
                problems.append("Please enter the city.")
            problems += contact_problems(phone, email)
            for problem in problems:
                st.error(problem, icon=":material/error:")
            if not problems:
                result = create_volunteer_from_api({
                    "volunteer_name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "address": address.strip(),
                    "city": city.strip(),
                })
                if "error" in result:
                    st.error(f"Could not add the volunteer: "
                             f"{result['error']}", icon=":material/error:")
                else:
                    ui.flash_success(
                        f"{name.strip()} was added. Next: assign them a "
                        "pickup under Pickup requests."
                    )

    if not volunteers:
        ui.empty_state("No volunteers yet. Add the first one above!",
                       icon=":material/directions_walk:", image="delivery")
        return

    ui.section_title(ui.plural(len(volunteers), "volunteer"),
                     ":material/directions_walk:", "teal")
    for column, volunteer in ui.grid(volunteers):
        (_, name, phone, email, address, city, availability, status,
         _created) = volunteer
        with column, ui.card():
            ui.person_header(name, [city])
            badges = [ui.badge_markdown("DISABLED" if status != "ACTIVE"
                                        else availability)]
            st.markdown(" ".join(badges))
            lines = []
            place = ", ".join(part for part in (address, city) if part)
            if place:
                lines.append(f":material/location_on: {place}")
            if phone:
                lines.append(f":material/call: [{phone}](tel:{phone})")
            if email:
                lines.append(f":material/mail: [{email}](mailto:{email})")
            st.markdown("  \n".join(lines) or "No contact details.")


# ---------------------------------------------------------------- user access

def user_access_page(ctx):
    now = now_local()
    pending = list_users(status="PENDING")
    ui.page_header(
        "User access",
        "Approve new people, and switch access on or off. "
        + (f"{ui.plural(len(pending), 'person', 'people')} waiting."
           if pending else "Nobody is waiting."),
        icon=":material/manage_accounts:",
    )
    st.info(
        "Anyone can sign in with Google. New people are approved by the "
        "ministry admin before they can use the app.",
        icon=":material/info:",
    )

    # 1. The next action: people waiting for approval.
    ui.section_title(f"Waiting for approval ({len(pending)})",
                     ":material/person_add:", "coral")
    if not pending:
        st.success("Nobody is waiting.", icon=":material/task_alt:")
    for column, person in ui.grid(pending):
        email = person["email"]
        with column, ui.card():
            ui.person_header(person["full_name"] or email, [person["city"]])
            st.markdown(ui.badge_markdown("PENDING")
                        + f" asked to join as "
                        f"**{ROLE_WORDS.get(person['role'], person['role'])}**")
            st.markdown(_contact_lines(person))
            chosen_role = st.selectbox(
                "Approve as", ROLES, index=ROLES.index(person["role"]),
                key=f"role_{email}", format_func=ROLE_WORDS.get,
            )
            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"approve_{email}",
                           type="primary", icon=":material/check:",
                           width="stretch"):
                try:
                    approve_user(email, chosen_role)
                    ui.flash_success(
                        f"{person['full_name'] or email} approved as "
                        f"{ROLE_WORDS[chosen_role]}. Next: they can sign in "
                        "and start."
                    )
                except ValueError as error:
                    st.error(str(error), icon=":material/error:")
            if col2.button("Decline", key=f"decline_{email}",
                           icon=":material/block:", width="stretch"):
                set_user_status(email, "DISABLED")
                ui.flash_success(f"{person['full_name'] or email} was "
                                 "declined.")

    # 2. Everyone else, as cards, with a search box.
    everyone = [p for p in list_users() if p["status"] != "PENDING"]
    ui.section_title(ui.plural(len(everyone), "person", "people"),
                     ":material/groups:", "purple")
    search = st.text_input("Find a person", placeholder="Name or email",
                           icon=":material/search:")
    if search.strip():
        needle = search.strip().lower()
        everyone = [p for p in everyone
                    if needle in (p["full_name"] or "").lower()
                    or needle in p["email"].lower()]
        if not everyone:
            st.caption("Nobody matches that search.")
    for column, person in ui.grid(everyone):
        email = person["email"]
        with column, ui.card():
            ui.person_header(person["full_name"] or email,
                             [ROLE_WORDS.get(person["role"], person["role"]),
                              person["city"]])
            st.markdown(
                ui.badge_markdown(person["status"])
                + f" **{ROLE_WORDS.get(person['role'], person['role'])}**"
            )
            lines = [_contact_lines(person)]
            lines.append(":material/login: Last signed in "
                         + (ui.friendly_time(person["last_login_at"], now)
                            if person["last_login_at"] else "never"))
            st.markdown("  \n".join(line for line in lines if line))
            if email == ctx.user["email"]:
                st.caption("This is you.")
            elif person["status"] == "ACTIVE":
                if st.button("Switch off access", key=f"off_{email}",
                             icon=":material/block:", width="stretch"):
                    set_user_status(email, "DISABLED")
                    ui.flash_success(f"{person['full_name'] or email} can "
                                     "no longer sign in.")
            elif st.button("Switch access back on", key=f"on_{email}",
                           icon=":material/check:", width="stretch"):
                set_user_status(email, "ACTIVE")
                ui.flash_success(f"{person['full_name'] or email} can sign "
                                 "in again.")


def _contact_lines(person):
    lines = [f":material/mail: [{person['email']}](mailto:{person['email']})"]
    if person["phone"]:
        lines.append(f":material/call: [{person['phone']}]"
                     f"(tel:{person['phone']})")
    if person["city"]:
        lines.append(f":material/location_on: {person['city']}")
    return "  \n".join(lines)
