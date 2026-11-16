"""Login for the Streamlit app.

Production: Google sign-in through Streamlit's built-in st.login().
It switches on when an [auth] section exists in Streamlit secrets
(see README "Set up Google login").

Local development only: set DEV_LOGIN=true to type any email instead of
signing in with Google. Never set DEV_LOGIN on the live app.

Anyone not set up yet can ask for access; an admin approves them.
Emails in ADMIN_EMAILS become admins automatically on first login.
"""

import streamlit as st

from app.config import get_list_setting, get_setting
from app.user_service import (
    SELF_SERVICE_ROLES,
    ensure_admin,
    get_user,
    normalize_email,
    record_login,
    request_access,
)

ROLE_LABELS = {
    "ADMIN": "Admin (ministry coordinator)",
    "DONOR": "Donor (restaurant, caterer or family with surplus food)",
    "ORGANIZATION": "Organization (NGO, home or charity receiving food)",
    "VOLUNTEER": "Volunteer (collects and delivers food)",
}


def _auth_mode():
    try:
        if "auth" in st.secrets:
            return "google"
    except Exception:
        pass
    if str(get_setting("DEV_LOGIN", "")).lower() == "true":
        return "dev"
    return None


def logout_button():
    if st.sidebar.button("Log out"):
        if _auth_mode() == "google":
            st.logout()
        else:
            st.session_state.pop("dev_email", None)
            st.session_state.pop("login_recorded", None)
            st.rerun()


def _signed_in_email():
    mode = _auth_mode()

    if mode == "google":
        if not st.user.is_logged_in:
            st.subheader("Please sign in")
            st.write(
                "This platform is for the ministry's donors, partner "
                "organizations and volunteers. Sign in with your Google "
                "account to continue."
            )
            if st.button("Sign in with Google", type="primary"):
                st.login()
            st.stop()
        return normalize_email(st.user.get("email")), st.user.get("name")

    if mode == "dev":
        email = st.session_state.get("dev_email")
        if not email:
            st.warning(
                "Development login is on (DEV_LOGIN=true). "
                "Do not use this on the live app."
            )
            with st.form("dev_login"):
                typed = st.text_input("Email to sign in as")
                if st.form_submit_button("Sign in"):
                    st.session_state["dev_email"] = normalize_email(typed)
                    st.rerun()
            st.stop()
        return email, None

    st.error(
        "Login is not configured yet, so the app is locked. "
        "Add the [auth] section to Streamlit secrets (see the README), "
        "or set DEV_LOGIN=true when testing on your own computer."
    )
    st.stop()


def _request_access_screen(email, name, existing):
    if existing and existing["status"] == "PENDING":
        st.info(
            f"Thanks, {existing['full_name'] or email}. Your request to join "
            f"as **{existing['role'].title()}** is waiting for an admin to "
            "approve it. Please check back later."
        )
        logout_button()
        st.stop()

    st.subheader("Request access")
    st.write(f"Signed in as **{email}**. Tell us how you'd like to help.")
    with st.form("request_access"):
        full_name = st.text_input("Your name", value=name or "")
        phone = st.text_input("Phone")
        city = st.text_input("City")
        role = st.radio(
            "I am a",
            SELF_SERVICE_ROLES,
            format_func=lambda value: ROLE_LABELS[value],
        )
        if st.form_submit_button("Send request", type="primary"):
            try:
                request_access(email, full_name, phone, city, role)
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    logout_button()
    st.stop()


def require_user():
    """Return the logged-in, approved user as a dict, or stop the page."""
    email, name = _signed_in_email()
    if not email:
        st.error("Your sign-in did not include an email address.")
        st.stop()

    admin_emails = {normalize_email(e) for e in get_list_setting("ADMIN_EMAILS")}
    if email in admin_emails:
        user = ensure_admin(email, name)
    else:
        user = get_user(email)

    if user is None or user["status"] == "PENDING":
        _request_access_screen(email, name, user)

    if user["status"] == "DISABLED":
        st.error("Your access has been switched off. Please contact an admin.")
        logout_button()
        st.stop()

    if not st.session_state.get("login_recorded"):
        record_login(email)
        st.session_state["login_recorded"] = True

    return user
