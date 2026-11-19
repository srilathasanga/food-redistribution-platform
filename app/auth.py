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
from app.privacy import MINISTRY_NAME, privacy_link_markdown
from app.ui import centered_card
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


def privacy_footer():
    st.caption(privacy_link_markdown())


def _log_out():
    if _auth_mode() == "google":
        st.logout()
    else:
        st.session_state.pop("dev_email", None)
        st.session_state.pop("login_recorded", None)
        st.rerun()


def logout_button():
    """Log out button in the sidebar (signed-in pages)."""
    if st.sidebar.button("Log out", icon=":material/logout:"):
        _log_out()


def _sign_out_link():
    """Sign out on the page itself: on phones the sidebar is hidden."""
    if st.button("Sign out / use a different account", type="tertiary",
                 icon=":material/logout:"):
        _log_out()


# How it works, in three short steps (sign-in screen).
_HOW_IT_WORKS = (
    (":material/soup_kitchen:", "Donors share surplus food"),
    (":material/apartment:", "Verified homes and shelters request it"),
    (":material/local_shipping:", "Volunteers pick it up and deliver it"),
)


def _welcome_hero():
    """Top of the sign-in card: who we are and what the app does."""
    st.markdown(f"### :material/volunteer_activism: {MINISTRY_NAME}")
    st.title("Share surplus food with neighbours in need")
    st.markdown(
        "We connect good food that would otherwise go to waste with "
        "homes and shelters nearby, delivered by volunteers."
    )
    st.markdown("  \n".join(
        f"{icon} {words}" for icon, words in _HOW_IT_WORKS
    ))


def _cant_sign_in_help():
    st.markdown(
        "**Can't sign in?** During the pilot only invited Gmail addresses "
        "can sign in. Ask the ministry admin to add your Gmail, then try "
        "again."
    )


def _signed_in_email():
    mode = _auth_mode()

    if mode == "google":
        if not st.user.is_logged_in:
            with centered_card():
                _welcome_hero()
                if st.button("Sign in with Google", type="primary",
                             icon=":material/login:", width="stretch"):
                    st.login()
                st.caption(
                    "Use the Google account (Gmail) the ministry admin "
                    "added for you."
                )
                _cant_sign_in_help()
                privacy_footer()
            st.stop()
        return normalize_email(st.user.get("email")), st.user.get("name")

    if mode == "dev":
        email = st.session_state.get("dev_email")
        if not email:
            with centered_card():
                st.warning(
                    "Development login is on (DEV_LOGIN=true). "
                    "Do not use this on the live app.",
                    icon=":material/construction:",
                )
                _welcome_hero()
                with st.form("dev_login", border=False):
                    typed = st.text_input("Email to sign in as")
                    if st.form_submit_button("Sign in", type="primary",
                                             icon=":material/login:",
                                             width="stretch"):
                        st.session_state["dev_email"] = normalize_email(typed)
                        st.rerun()
                privacy_footer()
            st.stop()
        return email, None

    st.error(
        "Login is not configured yet, so the app is locked. "
        "Add the [auth] section to Streamlit secrets (see the README), "
        "or set DEV_LOGIN=true when testing on your own computer."
    )
    st.stop()


# What each role does, in the person's own words (request-access form).
HELP_CHOICES = {
    "DONOR": "I have surplus food to share (restaurant, caterer or family)",
    "ORGANIZATION": "My organization receives food (home, shelter, NGO)",
    "VOLUNTEER": "I can pick up and deliver food (volunteer)",
}


def _hello(name):
    """'Welcome, Grace!' or just 'Welcome!' when we don't know the name."""
    first = (name or "").strip().split(" ")[0]
    return f", {first}" if first else ""


def _waiting_screen(email, existing):
    with centered_card():
        st.markdown("### :material/hourglass_top: Thanks for signing up!")
        st.markdown(
            f"Hi{_hello(existing['full_name'])}, your request "
            f"to join as **{existing['role'].title()}** is waiting for an "
            "admin to approve it."
        )
        st.markdown(
            "You don't need to do anything else. Please sign in again "
            "later; if it is urgent, contact the ministry admin."
        )
        st.caption(f"Signed in as {email}")
        _sign_out_link()
        privacy_footer()
    st.stop()


def _request_access_screen(email, name, existing):
    if existing and existing["status"] == "PENDING":
        _waiting_screen(email, existing)

    with centered_card():
        st.markdown(f"### :material/waving_hand: Welcome{_hello(name)}!")
        st.markdown(
            "Tell us a little about yourself. A ministry coordinator will "
            "check and approve your request."
        )
        st.caption(f"Signed in as {email}")
        with st.form("request_access", border=False):
            full_name = st.text_input("Your name", value=name or "")
            phone = st.text_input(
                "Phone",
                placeholder="e.g. 98765 43210",
                help="So the coordinator can reach you about pickups.",
            )
            city = st.text_input("City", placeholder="e.g. Hyderabad")
            role = st.radio(
                "How would you like to help?",
                SELF_SERVICE_ROLES,
                index=None,
                format_func=lambda value: HELP_CHOICES[value],
            )
            if st.form_submit_button("Send my request", type="primary",
                                     icon=":material/send:", width="stretch"):
                if not full_name.strip():
                    st.error("Please enter your name.")
                elif role is None:
                    st.error("Please choose how you would like to help.")
                else:
                    try:
                        request_access(email, full_name, phone, city, role)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
        _sign_out_link()
        privacy_footer()
    st.stop()


def _switched_off_screen(email):
    with centered_card():
        st.markdown("### :material/block: Your access is switched off")
        st.markdown(
            "An admin has switched off your account. If you think this is "
            "a mistake, please contact the ministry admin."
        )
        st.caption(f"Signed in as {email}")
        _sign_out_link()
        privacy_footer()
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
        _switched_off_screen(email)

    if not st.session_state.get("login_recorded"):
        record_login(email)
        st.session_state["login_recorded"] = True

    return user
