"""The admin Home numbers come from one query; check each number."""

from datetime import timedelta

from app.dashboard_service import get_admin_home_counts, get_urgent_food
from app.donation_service import add_food_donation
from app.food_risk_service import get_food_risk_analysis
from app.organization_service import add_organization
from app.user_service import request_access


def test_empty_database_counts_are_zero():
    assert set(get_admin_home_counts().values()) == {0}


def test_admin_home_counts(restaurant_id, make_donation, make_pickup, now):
    make_donation(expires_in_hours=1, food_name="Urgent rice")      # urgent
    make_donation(expires_in_hours=5, food_name="Bread")            # later
    requested = make_donation(expires_in_hours=8, food_name="Dal")
    make_pickup(requested)                                          # REQUESTED
    # Already expired, never collected.
    add_food_donation(restaurant_id, "Old curry", "Cooked", 2, "kg",
                      now - timedelta(hours=6), now - timedelta(hours=1),
                      "VEGETARIAN", "PACKED", "Rd")
    request_access("new@example.com", "New", "9", "Hyd", "DONOR")
    add_organization("Grace Home", "Ruth", "9", "g@example.com", "Rd",
                     "Hyd", "NGO")

    counts = get_admin_home_counts()
    assert counts == {
        "food_available": 3,       # urgent rice, bread, dal (not expired)
        "urgent": 1,
        "expired_uncollected": 1,
        "pickups_to_accept": 1,
        "people_to_approve": 1,
        "organizations_to_verify": 1,
    }
    assert [row[1] for row in get_urgent_food()] == ["Urgent rice"]


def test_urgent_matches_food_risk_service(make_donation):
    make_donation(expires_in_hours=1, food_name="Soon")
    make_donation(expires_in_hours=3, food_name="Later")
    high = [r["food_name"] for r in get_food_risk_analysis()
            if r["risk_level"] == "HIGH"]
    assert [row[1] for row in get_urgent_food()] == high == ["Soon"]
    assert get_admin_home_counts()["urgent"] == 1
