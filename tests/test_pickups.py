import threading
from datetime import timedelta

import pytest

from app.organization_service import add_organization
from app.pickup_service import (
    assign_volunteer,
    get_all_pickup_requests,
    get_pickup_summary,
    get_volunteer_pickups,
    request_pickup,
    update_pickup_status,
)
from app.volunteer_service import add_volunteer
from tests.conftest import query_one


def donation_status(donation_id):
    return query_one(
        "SELECT donation_status FROM food_donations WHERE donation_id = %s;",
        (donation_id,),
    )[0]


def volunteer_availability(volunteer_id):
    return query_one(
        "SELECT availability_status FROM volunteers WHERE volunteer_id = %s;",
        (volunteer_id,),
    )[0]


def test_complete_flow(make_donation, make_pickup, volunteer_id):
    donation_id = make_donation()
    pickup_id = make_pickup(donation_id)

    update_pickup_status(pickup_id, "ACCEPTED")
    assert donation_status(donation_id) == "RESERVED"

    assign_volunteer(pickup_id, volunteer_id)
    assert volunteer_availability(volunteer_id) == "BUSY"

    update_pickup_status(pickup_id, "PICKED_UP")
    assert donation_status(donation_id) == "PICKED_UP"

    update_pickup_status(pickup_id, "DELIVERED")
    assert donation_status(donation_id) == "DELIVERED"
    assert volunteer_availability(volunteer_id) == "AVAILABLE"
    assert get_pickup_summary()["delivered_pickups"] == 1


def test_steps_cannot_be_skipped(make_donation, make_pickup):
    pickup_id = make_pickup(make_donation())
    with pytest.raises(ValueError, match="Invalid transition"):
        update_pickup_status(pickup_id, "DELIVERED")


def test_duplicate_pickup_is_blocked(make_donation, make_pickup):
    donation_id = make_donation()
    make_pickup(donation_id)
    with pytest.raises(ValueError):
        make_pickup(donation_id)


def test_two_organizations_racing_for_one_donation(
    make_donation, verified_org_id, now
):
    # Row locking (FOR UPDATE) + the unique index allow only one winner.
    donation_id = make_donation()
    results = []

    def attempt():
        try:
            request_pickup(
                donation_id, verified_org_id, now + timedelta(hours=2),
                "addr", None,
            )
            results.append("ok")
        except ValueError:
            results.append("blocked")

    threads = [threading.Thread(target=attempt) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == ["blocked"] * 4 + ["ok"]


def test_unverified_organization_cannot_request(make_donation, now):
    organization_id = add_organization(
        "New NGO", "A", "1", "a@b.c", "x", "Hyderabad", "NGO"
    )
    with pytest.raises(ValueError, match="Only verified organizations"):
        request_pickup(
            make_donation(), organization_id, now + timedelta(hours=1),
            "addr", None,
        )


def test_pickup_time_uses_india_time(make_donation, make_pickup):
    # Before the fix the server compared against UTC, 5.5 hours behind
    # India, so a pickup time 1 hour in the past was accepted.
    donation_id = make_donation()
    with pytest.raises(ValueError, match="must be in the future"):
        make_pickup(donation_id, in_hours=-1)
    assert make_pickup(donation_id, in_hours=0.5)


def test_volunteer_needs_accepted_pickup(make_donation, make_pickup, volunteer_id):
    # Before the fix this raised a bare Exception -> "Internal Server Error".
    pickup_id = make_pickup(make_donation())
    with pytest.raises(ValueError, match="ACCEPTED pickup"):
        assign_volunteer(pickup_id, volunteer_id)


def test_busy_volunteer_cannot_take_second_pickup(
    make_donation, make_pickup, volunteer_id
):
    first = make_pickup(make_donation(food_name="Rice"))
    second = make_pickup(make_donation(food_name="Dal"))
    update_pickup_status(first, "ACCEPTED")
    update_pickup_status(second, "ACCEPTED")
    assign_volunteer(first, volunteer_id)
    with pytest.raises(ValueError, match="not available"):
        assign_volunteer(second, volunteer_id)


def test_pickup_cannot_get_two_volunteers(make_donation, make_pickup, volunteer_id):
    other = add_volunteer(
        volunteer_name="Sita", phone="6", email="", address="", city="Hyd"
    )
    pickup_id = make_pickup(make_donation())
    update_pickup_status(pickup_id, "ACCEPTED")
    assign_volunteer(pickup_id, volunteer_id)
    with pytest.raises(ValueError, match="already assigned"):
        assign_volunteer(pickup_id, other)


def test_pickup_list_filters(make_donation, make_pickup, volunteer_id,
                             verified_org_id):
    pickup_id = make_pickup(make_donation())
    make_pickup(make_donation(food_name="Dal"))
    update_pickup_status(pickup_id, "ACCEPTED")
    assign_volunteer(pickup_id, volunteer_id)

    assert len(get_all_pickup_requests()) == 2
    assert len(get_all_pickup_requests(organization_id=verified_org_id)) == 2
    assert len(get_all_pickup_requests(organization_id=999)) == 0
    mine = get_all_pickup_requests(volunteer_id=volunteer_id)
    assert [row[0] for row in mine] == [pickup_id]


def test_volunteer_sees_delivery_details_only_for_own_active_pickups(
        make_donation, make_pickup, volunteer_id):
    # A volunteer has one active pickup at a time (busy until delivered),
    # so finish the first one before assigning the second.
    done = make_pickup(make_donation(food_name="Dal"))
    update_pickup_status(done, "ACCEPTED")
    assign_volunteer(done, volunteer_id)
    update_pickup_status(done, "PICKED_UP")
    update_pickup_status(done, "DELIVERED")

    active = make_pickup(make_donation())
    update_pickup_status(active, "ACCEPTED")
    assign_volunteer(active, volunteer_id)

    someone_elses = make_pickup(make_donation(food_name="Not mine"))
    other_volunteer = add_volunteer(
        volunteer_name="Asha", phone="7000000000",
        email="asha@example.com", address="Begumpet", city="Hyderabad",
    )
    update_pickup_status(someone_elses, "ACCEPTED")
    assign_volunteer(someone_elses, other_volunteer)

    rows = {row[0]: row for row in get_volunteer_pickups(volunteer_id)}
    assert set(rows) == {active, done}            # never another's pickup
    assert rows[active][13:] == ("45 Church Street", "Mary", "8888888888")
    assert rows[done][13:] == (None, None, None)  # finished: hidden again


def test_volunteer_pickups_need_a_volunteer():
    with pytest.raises(ValueError):
        get_volunteer_pickups(None)
