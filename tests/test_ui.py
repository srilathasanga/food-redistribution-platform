"""Click through the real Streamlit pages as each role.

Uses Streamlit's built-in AppTest runner with development login
(DEV_LOGIN=true), so no Google account is needed.
"""

from datetime import timedelta

import pytest
from streamlit.testing.v1 import AppTest

from app.user_service import approve_user, get_user, request_access

ADMIN = "lead@church.org"


@pytest.fixture(autouse=True)
def dev_login(monkeypatch):
    monkeypatch.setenv("DEV_LOGIN", "true")
    monkeypatch.setenv("ADMIN_EMAILS", ADMIN)


def open_app(email=None, page=None):
    at = AppTest.from_file("app.py", default_timeout=30)
    if email:
        at.session_state["dev_email"] = email
    at.run()
    if page:
        at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    return at


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
    assert not at.sidebar.radio  # no menu before login


def test_admin_can_open_every_page():
    at = open_app(ADMIN)
    pages = at.sidebar.radio[0].options
    assert "User Access" in pages and "Admin" in pages
    for page in pages:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, (page, at.exception)
        assert not at.error, (page, [e.value for e in at.error])


def test_new_person_requests_access_and_waits():
    at = open_app("new@example.com")
    form_inputs = {t.label: t for t in at.text_input}
    form_inputs["Your name"].set_value("Grace")
    form_inputs["Phone"].set_value("9111111111")
    form_inputs["City"].set_value("Hyderabad")
    at.radio[0].set_value("DONOR")
    at.button[0].click().run()
    assert not at.exception
    assert "waiting for an admin" in all_text(at)
    assert get_user("new@example.com")["status"] == "PENDING"


def test_admin_approves_from_user_access_page():
    request_access("vol@example.com", "Ravi", "9222222222", "Hyd", "VOLUNTEER")
    at = open_app(ADMIN, "User Access")
    [approve] = [b for b in at.button if b.label == "Approve"]
    approve.click().run()
    assert not at.exception
    user = get_user("vol@example.com")
    assert user["status"] == "ACTIVE" and user["volunteer_id"]
    assert "approved" in all_text(at)


def test_donor_registers_restaurant_and_posts_food(now):
    make_user("donor@example.com", "DONOR")
    at = open_app("donor@example.com", "My Restaurant")
    assert at.sidebar.radio[0].options == [
        "Home", "My Restaurant", "Food Donations"
    ]
    inputs = {t.label: t for t in at.text_input}
    inputs["Restaurant / kitchen name"].set_value("St. Mark's Kitchen")
    at.text_area[0].set_value("12 Church Road")
    at.button[0].click().run()
    assert not at.exception
    assert get_user("donor@example.com")["restaurant_id"] is not None

    at.sidebar.radio[0].set_value("Food Donations").run()
    assert at.selectbox[0].options == [
        f"St. Mark's Kitchen (ID: {get_user('donor@example.com')['restaurant_id']})"
    ]
    inputs = {t.label: t for t in at.text_input}
    inputs["Food Name"].set_value("Chicken Biryani")
    inputs["Food Category"].set_value("Cooked Meals")
    at.number_input[0].set_value(5)
    at.date_input[1].set_value((now + timedelta(days=1)).date())
    [submit] = [b for b in at.button if b.label == "Create Food Donation"]
    submit.click().run()
    assert not at.exception
    assert "Chicken Biryani" in all_text(at)


def test_donor_cannot_see_admin_pages():
    make_user("donor2@example.com", "DONOR")
    at = open_app("donor2@example.com")
    options = at.sidebar.radio[0].options
    for page in ("Admin", "User Access", "Restaurants", "Pickup Requests"):
        assert page not in options


def test_organization_sees_only_own_pickups(make_donation, make_pickup,
                                            verified_org_id):
    make_user("ngo@example.com", "ORGANIZATION")
    # Another organization's pickup must stay hidden.
    make_pickup(make_donation())
    at = open_app("ngo@example.com", "Pickup Requests")
    assert "No pickup requests found." in all_text(at)
    assert "must be registered and verified" in all_text(at)
    assert not [b for b in at.button if b.label == "✅ Accept Pickup"]


def test_volunteer_marks_assigned_pickup_delivered(make_donation, make_pickup):
    from app.pickup_service import assign_volunteer, update_pickup_status

    make_user("vol2@example.com", "VOLUNTEER")
    volunteer_id = get_user("vol2@example.com")["volunteer_id"]
    pickup_id = make_pickup(make_donation())
    update_pickup_status(pickup_id, "ACCEPTED")
    assign_volunteer(pickup_id, volunteer_id)
    make_pickup(make_donation(food_name="Not mine"))

    at = open_app("vol2@example.com", "My Pickups")
    assert len(at.expander) == 1
    [picked] = [b for b in at.button if b.label == "📦 Mark Picked Up"]
    picked.click().run()
    [delivered] = [b for b in at.button if b.label == "🚚 Mark Delivered"]
    delivered.click().run()
    assert not at.exception
    assert "DELIVERED" in all_text(at)
    # No request form for volunteers.
    assert not [b for b in at.button if b.label == "🚚 Request Pickup"]


def test_admin_pages_with_data_and_admin_actions(make_donation, make_pickup,
                                                 volunteer_id):
    from app.organization_service import add_organization

    pending_org = add_organization(
        "Grace Home", "Ruth", "9333333333", "g@example.com", "Rd", "Hyd", "NGO"
    )
    make_donation(expires_in_hours=1, food_name="Urgent Curry")
    pickup_id = make_pickup(make_donation())

    at = open_app(ADMIN)
    for page in at.sidebar.radio[0].options:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, (page, at.exception)
        assert not at.error, (page, [e.value for e in at.error])

    # Verify the pending organization on the Admin page.
    at.sidebar.radio[0].set_value("Admin").run()
    [verify] = [b for b in at.button if b.key == f"verify_{pending_org}"]
    verify.click().run()
    assert "verified successfully" in all_text(at)

    # Accept the pickup, then assign the volunteer.
    at.sidebar.radio[0].set_value("Pickup Requests").run()
    [accept] = [b for b in at.button if b.key == f"accept_{pickup_id}"]
    accept.click().run()
    [assign] = [b for b in at.button
                if b.key == f"assign_volunteer_{pickup_id}"]
    assign.click().run()
    assert not at.exception
    assert "Volunteer assigned successfully" in all_text(at)


def test_privacy_page_is_public():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.query_params["page"] = "privacy"
    at.run()
    assert not at.exception, at.exception
    assert "Privacy policy" in [t.value for t in at.title]
    assert "never sell" in all_text(at)
    assert not at.sidebar.radio  # no login, no menu


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
