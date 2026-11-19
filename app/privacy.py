"""Public privacy policy page.

Shown at the app URL with ?page=privacy, for example
https://YOUR-APP.streamlit.app/?page=privacy

It needs no login and no database, so Google (and anyone else) can read
it even when the database is down.
"""

import streamlit as st

PRIVACY_QUERY_VALUE = "privacy"

# Relative link: works on localhost and on the live app without knowing
# the app's address.
PRIVACY_LINK = "?page=privacy"

# Shown here and on the sign-in screen. Change it in this one place.
MINISTRY_NAME = "Test Ministry"

LAST_UPDATED = "19 November 2026"

PRIVACY_POLICY = f"""
**{MINISTRY_NAME}** · Food Redistribution Platform

*Last updated: {LAST_UPDATED}*

This app is run by **{MINISTRY_NAME}**, a church food ministry. It
connects surplus food from restaurants, caterers and families with
verified organizations (homes, shelters, charities), and with volunteers
who collect and deliver the food. This page explains, in plain words,
what information we keep and how we look after it.

### Signing in with Google

You sign in with your Google account. Google tells us only your
**name** and **email address**. We never see or store your Google
password. The app keeps a small sign-in cookie in your browser so you
stay signed in; we do not use advertising or tracking cookies.

### What we collect

- **About you:** name, email address, phone number, city, the role you
  asked for (donor, organization or volunteer), and when you last
  signed in.
- **Restaurants and donors:** restaurant or donor name, contact person,
  phone, email, address and city.
- **Organizations:** organization name and type, contact person, phone,
  email, address, city and verification status.
- **Volunteers:** name, phone, email, address, city and whether you are
  available.
- **Donations and pickups:** what food is offered, how much, when it was
  prepared and when it expires, pickup address, pickup time, notes, and
  the status of each pickup and delivery.

### Why we collect it

Only to coordinate food donations, pickups and deliveries: so the right
food reaches the right organization safely and on time, and so the
ministry can see how much food has been shared.

### Who can see it

- **Ministry admins** can see everything, including contact details,
  so they can approve people and arrange pickups.
- **Donors, organizations and volunteers** see only their own
  information and the donations or pickups that involve them. They do
  not see other people's contact details.
- We **never sell, rent or share** your information with anyone outside
  the ministry, and we do not use it for advertising.

### Where it is stored

- The information is stored in a **Neon PostgreSQL** database in the
  **United States**.
- The app itself is hosted on **Streamlit Community Cloud**, also in the
  **United States**.
- Sign-in is handled by **Google**.

These services keep the data on our behalf and use encrypted
connections.

### How long we keep it

- We keep your information for **2 years after your last activity**
  in the app (for example your last sign-in, donation or pickup), and
  then delete it.
- If you ask us to delete your information, we do so within
  **30 days** of your request.

### Your choices: access, correction, deletion

You can ask to see the information we hold about you, to correct it, or
to delete it. Please contact the ministry admin:

- **Srilatha**, {MINISTRY_NAME}
- Email: [srilathasanga@gmail.com](mailto:srilathasanga@gmail.com)

### Changes to this policy

If we change this policy we will update the date at the top of this
page.
"""


def is_privacy_request():
    """True when the URL asks for the privacy page (?page=privacy)."""
    return st.query_params.get("page") == PRIVACY_QUERY_VALUE


def privacy_link_markdown():
    return f"[Privacy policy]({PRIVACY_LINK})"


def render_privacy_page():
    st.title("Privacy policy")
    st.markdown(PRIVACY_POLICY)
    if st.button("Back to the app"):
        st.query_params.clear()
        st.rerun()
