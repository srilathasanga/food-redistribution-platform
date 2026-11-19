"""Click through the real Streamlit pages as each role.

Uses Streamlit's built-in AppTest runner with development login
(DEV_LOGIN=true), so no Google account is needed.
"""

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from app.navigation import pages_for
from app.user_service import approve_user, get_user, request_access

ADMIN = "lead@church.org"


@pytest.fixture(autouse=True)
def dev_login(monkeypatch):
    """Use the local dev login and the test admin, whatever this
    computer's .streamlit/secrets.toml contains (it may have a Google
    [auth] section and the real ADMIN_EMAILS)."""
    import app.auth
    import app.config

    monkeypatch.setattr(app.auth, "_auth_mode", lambda: "dev")
    for name, value in (("DEV_LOGIN", "true"), ("ADMIN_EMAILS", ADMIN)):
        monkeypatch.setenv(name, value)
        # Start-up values win over secrets.toml (see app/config.py).
        monkeypatch.setitem(app.config._STARTUP_ENV, name, value)


def go_to(at, page):
    """Open a menu page by its address (see app/navigation.py).

    AppTest cannot click st.navigation links, so set the page directly.
    """
    at._page_hash = calc_hash(page)
    return at.run()


# Note: after a button that saves something, the app refreshes itself
# (ui.flash_success -> st.rerun). Streamlit's AppTest then keeps leftover
# elements from before the refresh (a real browser does not), so after
# such an action, open the next page with a fresh open_app(...) instead
# of go_to(...) on the same session.


def open_app(email=None, page=None):
    at = AppTest.from_file("app.py", default_timeout=30)
    if email:
        at.session_state["dev_email"] = email
    at.run()
    if page:
        go_to(at, page)
    assert not at.exception, at.exception
    return at


def signed_in(at):
    return "Log out" in [b.label for b in at.sidebar.button]


def all_text(at):
    parts = []
    for kind in ("markdown", "info", "success", "warning", "error",
                 "header", "subheader", "caption"):
        parts += [element.value for element in getattr(at, kind)]
    return "\n".join(str(part) for part in parts)


def make_user(email, role):
    request_access(email, "Test " + role.title(), "9000000000", "Hyderabad",
                   role)
    approve_user(email, role)


def test_signed_out_visitor_sees_login_only():
    at = open_app()
    assert "Email to sign in as" in [t.label for t in at.text_input]
    assert not signed_in(at)  # no menu before login


def test_admin_can_open_every_page():
    at = open_app(ADMIN)
    assert signed_in(at)
    pages = pages_for("ADMIN")
    assert "user-access" in pages and "admin" in pages
    for page in pages:
        go_to(at, page)
        assert not at.exception, (page, at.exception)
        assert not at.error, (page, [e.value for e in at.error])


def test_new_person_requests_access_and_waits():
    at = open_app("new@example.com")
    form_inputs = {t.label: t for t in at.text_input}
    form_inputs["Your name"].set_value("Grace")
    form_inputs["Phone"].set_value("9111111111")
    form_inputs["City"].set_value("Hyderabad")
    at.radio[0].set_value("DONOR")
    [send] = [b for b in at.button if b.label == "Send my request"]
    send.click().run()
    assert not at.exception
    assert "waiting for an admin" in all_text(at)
    assert get_user("new@example.com")["status"] == "PENDING"
    # On a phone the sidebar is hidden, so signing out is on the page.
    assert [b for b in at.button if b.label.startswith("Sign out")]


def test_request_access_asks_how_to_help():
    at = open_app("unsure@example.com")
    {t.label: t for t in at.text_input}["Your name"].set_value("Joy")
    [send] = [b for b in at.button if b.label == "Send my request"]
    send.click().run()
    assert "Please choose how you would like to help." in all_text(at)
    assert get_user("unsure@example.com") is None


def test_admin_approves_from_user_access_page():
    request_access("vol@example.com", "Ravi", "9222222222", "Hyd", "VOLUNTEER")
    at = open_app(ADMIN, "user-access")
    [approve] = [b for b in at.button if b.label == "Approve"]
    approve.click().run()
    assert not at.exception
    user = get_user("vol@example.com")
    assert user["status"] == "ACTIVE" and user["volunteer_id"]
    assert "approved" in all_text(at)


def test_donor_registers_restaurant_and_posts_food():
    make_user("donor@example.com", "DONOR")
    assert pages_for("DONOR") == ["home", "my-restaurant", "donations"]
    at = open_app("donor@example.com", "my-restaurant")
    inputs = {t.label: t for t in at.text_input}
    inputs["Restaurant or kitchen name"].set_value("St. Mark's Kitchen")
    at.text_area[0].set_value("12 Church Road")
    [save] = [b for b in at.button if b.label == "Save my kitchen"]
    save.click().run()
    assert not at.exception
    assert get_user("donor@example.com")["restaurant_id"] is not None
    assert "Next:" in all_text(at)  # success says what happens next

    at = open_app("donor@example.com", "donations")  # fresh, see note above
    assert "Sharing from **St. Mark's Kitchen**" in all_text(at)
    {t.label: t for t in at.text_input}["What food is it?"].set_value(
        "Chicken Biryani")
    at.number_input[0].set_value(5)
    [share] = [b for b in at.button if b.label == "Share this food"]
    share.click().run()
    assert not at.exception
    assert "Chicken Biryani" in all_text(at)


def test_share_food_form_says_what_to_fix():
    make_user("donor3@example.com", "DONOR")
    at = open_app("donor3@example.com", "my-restaurant")
    {t.label: t for t in at.text_input}[
        "Restaurant or kitchen name"].set_value("Grace Kitchen")
    [b for b in at.button if b.label == "Save my kitchen"][0].click().run()
    at = open_app("donor3@example.com", "donations")  # fresh, see note above
    at.text_area[0].set_value("")  # no pickup address
    [b for b in at.button if b.label == "Share this food"][0].click().run()
    text = all_text(at)
    assert "Please say what the food is." in text
    assert "Please enter how much food there is." in text
    assert "Please add the pickup address" in text


def test_donor_cannot_see_admin_pages():
    make_user("donor2@example.com", "DONOR")
    for page in ("admin", "user-access", "restaurants", "pickups",
                 "volunteers"):
        assert page not in pages_for("DONOR")
        # Typing the address of an admin page only shows the donor's Home.
        at = open_app("donor2@example.com", page)
        assert "Good" in at.title[0].value  # "Good morning, Test!"
        assert not [b for b in at.button if b.label == "Approve"]


def test_organization_sees_only_own_pickups(make_donation, make_pickup,
                                            verified_org_id):
    make_user("ngo@example.com", "ORGANIZATION")
    # Another organization's pickup must stay hidden.
    make_pickup(make_donation(food_name="Someone else's food"))
    at = open_app("ngo@example.com", "pickups")
    assert "must be registered and verified" in all_text(at)
    assert "Someone else's food" not in all_text(at)
    assert not [b for b in at.button if (b.key or "").startswith("accept_")]


def test_verified_organization_can_request_food(make_donation,
                                                verified_org_id):
    from app.user_service import link_organization

    make_user("hope@example.com", "ORGANIZATION")
    link_organization("hope@example.com", verified_org_id)
    make_donation(food_name="Fresh Bread")
    at = open_app("hope@example.com", "available-food")
    assert "Fresh Bread" in all_text(at)
    assert [b for b in at.button if b.label == "Request this food"]


def test_volunteer_marks_assigned_pickup_delivered(make_donation, make_pickup):
    from app.pickup_service import assign_volunteer, update_pickup_status
    from tests.conftest import query_one

    make_user("vol2@example.com", "VOLUNTEER")
    volunteer_id = get_user("vol2@example.com")["volunteer_id"]
    pickup_id = make_pickup(make_donation())
    update_pickup_status(pickup_id, "ACCEPTED")
    assign_volunteer(pickup_id, volunteer_id)
    make_pickup(make_donation(food_name="Not mine"))

    at = open_app("vol2@example.com", "pickups")
    assert "Not mine" not in all_text(at)
    assert "45 Church Street" in all_text(at)  # delivery address shown
    [picked] = [b for b in at.button if b.key == f"progress_{pickup_id}"]
    assert picked.label == "Picked up"
    picked.click().run()
    assert "picked up. Next: deliver it" in all_text(at)
    at = open_app("vol2@example.com", "pickups")  # fresh, see note above
    [delivered] = [b for b in at.button if b.key == f"progress_{pickup_id}"]
    assert delivered.label == "Delivered"
    delivered.click().run()
    assert not at.exception
    assert "Thank you for serving" in all_text(at)
    assert query_one("SELECT pickup_status FROM pickup_requests "
                     "WHERE pickup_id = %s;", (pickup_id,))[0] == "DELIVERED"
    # No request form for volunteers.
    assert not [b for b in at.button if b.label == "Send request"]


def test_admin_pages_with_data_and_admin_actions(make_donation, make_pickup,
                                                 volunteer_id):
    from app.organization_service import add_organization

    pending_org = add_organization(
        "Grace Home", "Ruth", "9333333333", "g@example.com", "Rd", "Hyd", "NGO"
    )
    make_donation(expires_in_hours=1, food_name="Urgent Curry")
    pickup_id = make_pickup(make_donation())

    at = open_app(ADMIN)
    assert "Urgent Curry" in all_text(at)  # urgent food on Home
    for page in pages_for("ADMIN"):
        go_to(at, page)
        assert not at.exception, (page, at.exception)
        assert not at.error, (page, [e.value for e in at.error])

    # Verify the pending organization on the Organizations page.
    go_to(at, "organizations")
    [verify] = [b for b in at.button if b.key == f"verify_{pending_org}"]
    verify.click().run()
    assert "Grace Home is verified" in all_text(at)

    # Accept the pickup, then assign the volunteer (fresh sessions after
    # each saving click, see the note at the top).
    at = open_app(ADMIN, "pickups")
    [accept] = [b for b in at.button if b.key == f"accept_{pickup_id}"]
    accept.click().run()
    at = open_app(ADMIN, "pickups")
    [assign] = [b for b in at.button
                if b.key == f"assign_volunteer_{pickup_id}"]
    assign.click().run()
    assert not at.exception
    assert "Volunteer assigned" in all_text(at)


def test_privacy_page_is_public():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.query_params["page"] = "privacy"
    at.run()
    assert not at.exception, at.exception
    assert "Privacy policy" in [t.value for t in at.title]
    assert "never sell" in all_text(at)
    assert not signed_in(at)  # no login, no menu


def test_login_screen_links_to_privacy_policy():
    at = open_app()
    assert "?page=privacy" in all_text(at)


def test_friendly_message_when_database_is_down(monkeypatch):
    import app.schema

    def broken():
        raise RuntimeError("database unreachable")

    monkeypatch.setattr(app.schema, "ensure_schema", broken)
    import streamlit as st
    st.cache_resource.clear()
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception, at.exception
    assert "can't reach the app's database" in all_text(at)
    assert "Try again" in [b.label for b in at.button]
    st.cache_resource.clear()
