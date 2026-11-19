"""People: User access (admin only)."""

import streamlit as st

from app import ui
from app.timeutil import now_local
from app.user_service import ROLES, approve_user, list_users, set_user_status

ROLE_WORDS = {"ADMIN": "Admin", "DONOR": "Donor",
              "ORGANIZATION": "Organization", "VOLUNTEER": "Volunteer"}


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
        "New people must first be added as test users in Google Cloud → "
        "Google Auth Platform → Audience → Test users.",
        icon=":material/info:",
    )

    # 1. The next action: people waiting for approval.
    st.subheader("Waiting for approval")
    if not pending:
        st.success("Nobody is waiting.", icon=":material/task_alt:")
    for column, person in ui.grid(pending):
        email = person["email"]
        with column, ui.card():
            st.markdown(f"#### {person['full_name'] or email}")
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
    st.subheader(ui.plural(len(everyone), "person", "people"))
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
            st.markdown(f"#### {person['full_name'] or email}")
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
