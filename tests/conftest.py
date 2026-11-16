"""Shared test setup.

The tests need a SEPARATE, throw-away PostgreSQL database, because every
test empties all tables first. Point TEST_DATABASE_URL at it, e.g.

    TEST_DATABASE_URL=postgresql://postgres:secret@localhost:5432/food_test

(A free Neon "branch" also works.) Tests are skipped if it is not set, so
they can never wipe the real database by accident.
"""

import os
from datetime import timedelta

import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    # Make the app use the test database, whatever .env says.
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ.setdefault("APP_TIMEZONE", "Asia/Kolkata")

TABLES = (
    "app_users, pickup_requests, food_donations, "
    "restaurants, organizations, volunteers"
)


@pytest.fixture(autouse=True)
def clean_database():
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run database tests.")

    from app.database import get_connection
    from app.schema import ensure_schema

    ensure_schema()
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE;")
    connection.commit()
    cursor.close()
    connection.close()
    yield


# ------------------------------------------------------------ data helpers

@pytest.fixture
def now():
    from app.timeutil import now_local

    return now_local()


@pytest.fixture
def restaurant_id():
    from app.restaurant_service import add_restaurant

    return add_restaurant(
        "Green Leaf Restaurant", "Anil Kumar", "9999999999",
        "greenleaf@example.com", "123 Main Road", "Hyderabad",
    )


@pytest.fixture
def verified_org_id():
    from app.organization_service import add_organization, verify_organization

    organization_id = add_organization(
        "Hope Shelter", "Mary", "8888888888", "hope@example.com",
        "45 Church Street", "Hyderabad", "NGO",
    )
    verify_organization(organization_id)
    return organization_id


@pytest.fixture
def volunteer_id():
    from app.volunteer_service import add_volunteer

    return add_volunteer(
        volunteer_name="Ravi", phone="7777777777",
        email="ravi@example.com", address="Ameerpet", city="Hyderabad",
    )


@pytest.fixture
def make_donation(restaurant_id, now):
    from app.donation_service import add_food_donation

    def _make(expires_in_hours=6, food_name="Vegetable Rice"):
        return add_food_donation(
            restaurant_id, food_name, "Cooked Meals", 20, "kg",
            now - timedelta(hours=1),
            now + timedelta(hours=expires_in_hours),
            "VEGETARIAN", "PACKED", "123 Main Road, Hyderabad",
        )

    return _make


@pytest.fixture
def make_pickup(verified_org_id, now):
    from app.pickup_service import request_pickup

    def _make(donation_id, in_hours=2):
        return request_pickup(
            donation_id, verified_org_id, now + timedelta(hours=in_hours),
            "123 Main Road, Hyderabad", "test pickup",
        )

    return _make


def query_one(sql, params=()):
    from app.database import get_connection

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()
