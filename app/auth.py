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

# Reads are cached (the sign-in check for at most 20 seconds) and writes
# clear the caches: see app/backend.py.
from app.backend import ensure_admin, get_user, record_login, request_access
from app.config import get_list_setting, get_setting
from app import ui
from app.privacy import (
    CONTACT_EMAIL,
    MINISTRY_NAME,
    PRIVACY_LINK,
    privacy_link_markdown,
)
from app.ui import centered_card
from app.user_service import SELF_SERVICE_ROLES, normalize_email

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
    """Compact Log out button. Call it inside the sidebar (with
    st.sidebar: ...), e.g. in the profile card."""
    if st.button("Log out", icon=":material/logout:", key="log_out"):
        _log_out()


def _sign_out_link():
    """Sign out on the page itself: on phones the sidebar is hidden."""
    if st.button("Sign out / use a different account", type="tertiary",
                 icon=":material/logout:"):
        _log_out()


# The sign-in landing page: what the app does, who it is for, and ONE
# call to action (Sign in with Google). Words kept short on purpose.
HEADLINE = "Share surplus food with neighbours in need"
SUBLINE = ("Good food that would go to waste reaches homes and shelters "
           "nearby, delivered by volunteers.")

# (step, title, icon, tone, one line)
HOW_IT_WORKS = (
    ("Step 1", "Share surplus food", ":material/soup_kitchen:", "green",
     "Donors post the food they have to spare, in a minute."),
    ("Step 2", "Homes request it", ":material/apartment:", "purple",
     "Verified homes and shelters ask for what they can use."),
    ("Step 3", "Volunteers deliver", ":material/local_shipping:", "coral",
     "A volunteer picks it up and brings it while it is fresh."),
)
WHO_CAN_JOIN = (
    (None, "Donors", ":material/storefront:", "green",
     "Restaurants, caterers and families with good food to spare."),
    (None, "Homes and shelters", ":material/home:", "purple",
     "Homes, shelters and charities that feed people every day."),
    (None, "Volunteers", ":material/directions_walk:", "coral",
     "People who can pick up food and drop it off nearby."),
)


def _google_button(key):
    """The one call to action. Google's G is added by CSS (app/ui.py)."""
    if st.button("Sign in with Google", type="primary", key=key):
        st.login()


def _dev_login_form():
    st.warning("Development login is on (DEV_LOGIN=true). Do not use this "
               "on the live app.", icon=":material/construction:")
    with st.form("dev_login", border=False):
        typed = st.text_input("Email to sign in as")
        if st.form_submit_button("Sign in", type="primary",
                                 icon=":material/login:"):
            st.session_state["dev_email"] = normalize_email(typed)
            st.rerun()


def _landing_page(mode):
    """Hero with the sign-in button, How it works, Who can join, help and
    a slim footer. No database calls."""
    ui.landing_style()
    with st.container(key="landing-hero"):
        words, picture = st.columns([11, 9], gap="large",
                                    vertical_alignment="center")
        with words:
            st.html(ui.hero_text_html(MINISTRY_NAME, HEADLINE, SUBLINE,
                                      highlight="neighbours in need"))
            if mode == "google":
                _google_button("google_sign_in")
            else:
                _dev_login_form()
            st.html('<p class="fr-muted">For donors, partner homes and '
                    "volunteers</p>")
        with picture:
            st.html(ui.hero_picture_html("signin"))

    st.html('<h2 class="fr-landing-h2">How it works</h2>')
    ui.info_cards(HOW_IT_WORKS, "how")
    st.html('<h2 class="fr-landing-h2">Who can join</h2>')
    ui.info_cards(WHO_CAN_JOIN, "join")

    if mode == "google":
        # Phones only: after scrolling, the button is here again.
        with st.container(key="phone-only"):
            _google_button("google_sign_in_bottom")

    st.write("")
    with st.expander("Trouble signing in?", icon=":material/help:"):
        st.markdown(
            "Anyone can sign in with Google. New people are approved by "
            "the ministry admin before they can use the app.  \n"
            "If the Google window shows an error or closes, please try "
            "again. Still stuck? Write to the ministry admin (the email "
            "address is at the bottom of this page)."
        )
    st.html(ui.footer_html(MINISTRY_NAME, PRIVACY_LINK, CONTACT_EMAIL))


def _signed_in_email():
    mode = _auth_mode()

    if mode == "google":
        if not st.user.is_logged_in:
            _landing_page("google")
            st.stop()
        return normalize_email(st.user.get("email")), st.user.get("name")

    if mode == "dev":
        email = st.session_state.get("dev_email")
        if not email:
            _landing_page("dev")
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


def _signed_out_card():
    """Same look as the landing page: light background, brand row, card."""
    ui.landing_style()
    st.html('<div style="display:flex;justify-content:center;'
            'margin-bottom:.5rem">' + ui.brand_row_html(MINISTRY_NAME)
            + "</div>")
    return centered_card()


def _waiting_screen(email, existing):
    with _signed_out_card():
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

    with _signed_out_card():
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
    with _signed_out_card():
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
    user = get_user(email)
    if email in admin_emails and not (
            user and user["role"] == "ADMIN" and user["status"] == "ACTIVE"):
        # Only write when the admin's row is missing or needs fixing,
        # not on every click.
        user = ensure_admin(email, name)

    if user is None or user["status"] == "PENDING":
        _request_access_screen(email, name, user)

    if user["status"] == "DISABLED":
        _switched_off_screen(email)

    if not st.session_state.get("login_recorded"):
        record_login(email)
        st.session_state["login_recorded"] = True

    return user
