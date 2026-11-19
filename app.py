"""The Streamlit website: set-up, sign-in and the menu.

The pages themselves live in app/home_pages.py and app/screens/. Which
role sees which page is listed in app/navigation.py.
"""

import logging

import psycopg2
import streamlit as st

from app import ui
from app.auth import ROLE_LABELS, logout_button, require_user
from app.backend import get_organization, get_restaurant
from app.database import is_configured
from app.home_pages import show_home
from app.navigation import MENU, PAGES, pages_for, title_for
from app.privacy import (
    is_privacy_request,
    privacy_link_markdown,
    render_privacy_page,
)
from app.schema import ensure_schema
from app.screens import PageContext
from app.screens.food import available_food_page, donations_page
from app.screens.kitchens import my_restaurant_page, restaurants_page
from app.screens.organizations import (
    my_organization_page,
    organizations_page,
)
from app.screens.people import user_access_page, volunteers_page
from app.screens.pickups import pickups_page
from app.screens.reports import reports_page

# =========================================================
# STREAMLIT PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Food Redistribution Platform",
    page_icon="🍲",
    layout="wide"
)

ui.apply_style()


# Public privacy policy (?page=privacy). It must work without login and
# without the database, so it runs before both.
if is_privacy_request():
    render_privacy_page()
    st.stop()


@st.cache_resource(show_spinner="Preparing the database...")
def prepare_database():
    # Creates any missing tables once per server start.
    ensure_schema()
    return True


logger = logging.getLogger("food_app")


def database_unavailable_screen():
    """Friendly message instead of a Python traceback. Stops the page."""
    st.title("🍲 Food Redistribution Platform")
    st.error(
        "We can't reach the app's database right now, so the app is "
        "paused. Your information is safe.",
        icon=":material/cloud_off:",
    )
    st.markdown(
        "**Please try again in a minute.** If it keeps happening, tell "
        "the ministry admin."
    )
    if st.button("Try again", type="primary"):
        st.rerun()
    with st.expander("For the admin: how to fix this"):
        if not is_configured():
            st.markdown(
                "No database is set up. Add `DATABASE_URL` (the Neon "
                "connection string) to the Streamlit secrets, or to `.env` "
                "on your own computer."
            )
        else:
            st.markdown(
                "- Check that `DATABASE_URL` in the Streamlit secrets is "
                "correct (copy it again from the Neon dashboard).\n"
                "- Check that the Neon project is running.\n"
                "- The exact error is in the app logs (Streamlit Cloud: "
                "**Manage app** → logs)."
            )
    st.caption(privacy_link_markdown())
    st.stop()


try:
    prepare_database()
except Exception:
    # Not cached when it fails, so the next visit tries again.
    logger.exception("Could not prepare the database")
    database_unavailable_screen()


# =========================================================
# LOGIN
# =========================================================

try:
    user = require_user()
except psycopg2.Error:
    logger.exception("Database error while signing in")
    database_unavailable_screen()
role = user["role"]

ui.show_flash()

ctx = PageContext(
    user=user,
    my_restaurant=(get_restaurant(user["restaurant_id"])
                   if user["restaurant_id"] else None),
    my_organization=(get_organization(user["organization_id"])
                     if user["organization_id"] else None),
)


# =========================================================
# MENU (each role sees only its own pages: see app/navigation.py)
# =========================================================

def home_page(ctx):
    show_home(ctx.user, ctx.my_restaurant, ctx.my_organization, ctx.pages,
              ui.flash_success)


PAGE_FUNCTIONS = {
    "home": home_page,
    "my-restaurant": my_restaurant_page,
    "my-organization": my_organization_page,
    "available-food": available_food_page,
    "donations": donations_page,
    "pickups": pickups_page,
    "restaurants": restaurants_page,
    "organizations": organizations_page,
    "volunteers": volunteers_page,
    "admin": reports_page,
    "user-access": user_access_page,
}


def only_for_this_role(path, page_function):
    """Extra safety: never draw a page that is not in this role's menu."""
    def guarded_page():
        if path not in pages_for(role):
            st.error("You do not have access to this page.")
            st.stop()
        page_function(ctx)

    return guarded_page


def build_menu():
    menu = {}
    for section, paths in MENU[role].items():
        menu[section] = []
        for path in paths:
            # Kept in ctx.pages so pages can link to each other.
            ctx.pages[path] = st.Page(
                only_for_this_role(path, PAGE_FUNCTIONS[path]),
                title=title_for(role, path),
                icon=PAGES[path][1],
                url_path=path,
                default=(path == "home"),
            )
            menu[section].append(ctx.pages[path])
    return menu


current_page = st.navigation(build_menu(), position="sidebar")

st.sidebar.markdown(
    f"**{user['full_name'] or user['email']}**  \n"
    f"{ROLE_LABELS[role]}"
)
logout_button()
st.sidebar.caption(privacy_link_markdown())

current_page.run()
