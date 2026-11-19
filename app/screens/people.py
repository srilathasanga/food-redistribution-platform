"""People: User access (admin only)."""

import streamlit as st

from app import ui
from app.user_service import (
    ROLES,
    approve_user,
    list_users,
    set_user_status,
)

flash_success = ui.flash_success


def user_access_page(ctx):
    user = ctx.user
    role = ctx.role

    st.header("🔐 User Access")

    st.info(
        "New people must first be added as test users in Google Cloud → "
        "Google Auth Platform → Audience → Test users.",
        icon=":material/info:",
    )

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
