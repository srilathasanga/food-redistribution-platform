from datetime import timedelta

import pytest

from app.donation_service import (
    add_food_donation,
    get_available_donations,
    get_donation_summary,
    get_donations_for_restaurant,
    get_requestable_donations,
)


def donation_args(restaurant_id, now, **changes):
    args = dict(
        restaurant_id=restaurant_id,
        food_name="Vegetable Rice",
        food_category="Cooked Meals",
        quantity=10,
        unit="kg",
        prepared_time=now - timedelta(hours=1),
        expiry_time=now + timedelta(hours=5),
        food_type="VEGETARIAN",
        packaging_status="PACKED",
        pickup_address="123 Main Road",
    )
    args.update(changes)
    return args


def test_valid_donation_is_available(restaurant_id, now):
    donation_id = add_food_donation(**donation_args(restaurant_id, now))
    available = get_available_donations()
    assert [row[0] for row in available] == [donation_id]
    assert get_donation_summary()["available_donations"] == 1


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"food_name": ""}, "Food name is required"),
        ({"quantity": 0}, "Quantity must be greater than 0"),
        ({"food_type": "VEGAN"}, "Invalid food type"),
        ({"packaging_status": "OPEN"}, "Invalid packaging status"),
    ],
)
def test_invalid_donations_are_rejected(restaurant_id, now, changes, message):
    with pytest.raises(ValueError, match=message):
        add_food_donation(**donation_args(restaurant_id, now, **changes))


def test_expiry_must_be_after_preparation(restaurant_id, now):
    with pytest.raises(ValueError, match="Expiry time must be after"):
        add_food_donation(
            **donation_args(
                restaurant_id, now,
                expiry_time=now - timedelta(hours=2),
            )
        )


def test_unknown_restaurant_is_rejected(now):
    with pytest.raises(ValueError, match="Restaurant not found"):
        add_food_donation(**donation_args(9999, now))


def test_expired_food_is_not_listed(restaurant_id, now):
    add_food_donation(
        **donation_args(
            restaurant_id, now,
            prepared_time=now - timedelta(hours=5),
            expiry_time=now - timedelta(minutes=30),
        )
    )
    assert get_available_donations() == []


def test_donor_sees_own_recent_donations_newest_first(restaurant_id, now):
    from app.restaurant_service import add_restaurant

    other = add_restaurant("Other Kitchen", "X", "1", "x@example.com",
                           "Rd", "Hyd")
    first = add_food_donation(**donation_args(restaurant_id, now))
    second = add_food_donation(**donation_args(restaurant_id, now,
                                               food_name="Dal"))
    add_food_donation(**donation_args(other, now, food_name="Not mine"))

    mine = get_donations_for_restaurant(restaurant_id)
    assert [row[0] for row in mine] == [second, first]
    assert mine[0][5] == "AVAILABLE"
    assert get_donations_for_restaurant(restaurant_id, limit=1)[0][0] == second


def test_requested_food_is_no_longer_offered(make_donation, make_pickup):
    free = make_donation(food_name="Still free")
    taken = make_donation(food_name="Already requested")
    make_pickup(taken)

    offered = get_requestable_donations()
    assert [row[0] for row in offered] == [free]
    assert offered[0][12] == "Hyderabad"  # restaurant city
    # The older list still shows both (it ignores pickup requests).
    assert {row[0] for row in get_available_donations()} == {free, taken}
