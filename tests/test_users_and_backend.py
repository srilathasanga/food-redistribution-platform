from datetime import timedelta

import pytest

from app import backend
from app.food_risk_service import calculate_food_risk
from app.schema import ensure_schema
from app.user_service import (
    approve_user,
    ensure_admin,
    get_user,
    list_users,
    request_access,
    set_user_status,
)


# -------------------------------------------------------------------- users

def test_request_and_approve_volunteer_creates_volunteer_record():
    request_access("Ravi@Example.com ", "Ravi", "7777777777", "Hyderabad",
                   "VOLUNTEER")
    user = get_user("ravi@example.com")
    assert user["status"] == "PENDING"
    assert [u["email"] for u in list_users(status="PENDING")] == [
        "ravi@example.com"
    ]

    approved = approve_user("ravi@example.com", "VOLUNTEER")
    assert approved["status"] == "ACTIVE"
    assert approved["volunteer_id"] is not None


def test_people_cannot_ask_to_be_admin():
    with pytest.raises(ValueError):
        request_access("x@example.com", "X", "1", "Hyd", "ADMIN")


def test_bootstrap_admin_and_disable():
    admin = ensure_admin("lead@church.org", "Lead")
    assert (admin["role"], admin["status"]) == ("ADMIN", "ACTIVE")
    request_access("d@example.com", "D", "1", "Hyd", "DONOR")
    approve_user("d@example.com", "DONOR")
    set_user_status("d@example.com", "DISABLED")
    assert get_user("d@example.com")["status"] == "DISABLED"


def test_schema_can_run_twice():
    ensure_schema()
    ensure_schema()


# ------------------------------------------------------------------ backend

def test_backend_returns_api_shapes(make_donation):
    make_donation()
    donations = backend.get_available_donations_from_api()["donations"]
    row = donations[0]
    assert isinstance(row, list)
    assert isinstance(row[4], float)          # quantity: Decimal -> float
    assert isinstance(row[7], str) and "T" in row[7]  # expiry: ISO string


def test_backend_turns_rule_errors_into_messages(make_donation, make_pickup,
                                                 volunteer_id):
    pickup_id = make_pickup(make_donation())
    result = backend.assign_volunteer_to_pickup_from_api(pickup_id, volunteer_id)
    assert "ACCEPTED" in result["error"]


def test_backend_create_pickup_parses_iso_time(make_donation, verified_org_id,
                                               now):
    result = backend.create_pickup_from_api({
        "donation_id": make_donation(),
        "organization_id": verified_org_id,
        "pickup_time": (now + timedelta(hours=1)).isoformat(),
        "pickup_address": "addr",
        "notes": "",
    })
    assert result["pickup_id"] == 1


# --------------------------------------------------------------------- risk

@pytest.mark.parametrize(
    "hours, level",
    [(-1, "EXPIRED"), (1, "HIGH"), (4, "MEDIUM"), (10, "LOW")],
)
def test_food_risk_levels(now, hours, level):
    assert calculate_food_risk(now + timedelta(hours=hours))["risk_level"] == level
