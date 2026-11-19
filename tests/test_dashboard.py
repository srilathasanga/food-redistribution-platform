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
        "pickups_needing_volunteer": 0,
        "people_to_approve": 1,
        "organizations_to_verify": 1,
    }
    assert [row[1] for row in get_urgent_food()] == ["Urgent rice"]


def test_pickups_needing_a_volunteer(make_donation, make_pickup,
                                     volunteer_id):
    from app.pickup_service import assign_volunteer, update_pickup_status

    waiting = make_pickup(make_donation(food_name="Waiting"))
    update_pickup_status(waiting, "ACCEPTED")                # no volunteer
    covered = make_pickup(make_donation(food_name="Covered"))
    update_pickup_status(covered, "ACCEPTED")
    assign_volunteer(covered, volunteer_id)
    counts = get_admin_home_counts()
    assert counts["pickups_needing_volunteer"] == 1
    assert counts["pickups_to_accept"] == 0


def test_urgent_matches_food_risk_service(make_donation):
    make_donation(expires_in_hours=1, food_name="Soon")
    make_donation(expires_in_hours=3, food_name="Later")
    high = [r["food_name"] for r in get_food_risk_analysis()
            if r["risk_level"] == "HIGH"]
    assert [row[1] for row in get_urgent_food()] == high == ["Soon"]
    assert get_admin_home_counts()["urgent"] == 1


def test_impact_summary(restaurant_id, make_donation, make_pickup, now,
                        volunteer_id):
    from app.dashboard_service import get_impact_summary
    from app.pickup_service import assign_volunteer, update_pickup_status

    month_start = now.replace(day=1, hour=0, minute=0, second=0,
                              microsecond=0)
    assert get_impact_summary(month_start)["deliveries"] == 0

    donation = make_donation()                       # 20 kg
    add_food_donation(restaurant_id, "Chapati", "Bread", 50, "pieces",
                      now - timedelta(hours=1), now + timedelta(hours=3),
                      "VEGETARIAN", "PACKED", "Rd")  # not kg
    pickup = make_pickup(donation)
    update_pickup_status(pickup, "ACCEPTED")
    assign_volunteer(pickup, volunteer_id)
    update_pickup_status(pickup, "PICKED_UP")
    update_pickup_status(pickup, "DELIVERED")

    impact = get_impact_summary(month_start)
    assert impact == {
        "kg_this_month": 20.0,
        "donations_this_month": 2,
        "deliveries": 1,
        "kitchens": 1,
        "volunteers": 1,
        "organizations": 1,
    }
