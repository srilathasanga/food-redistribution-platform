"""Cached reads (app/backend.py) and the connection pool (app/database.py).

No database needed: the service functions are replaced by stand-ins that
count how often they are really called.
"""

import types

import pytest

import app.backend as backend
import app.database as database
import app.user_service as user_service

pytestmark = pytest.mark.no_database


class Counter:
    """A stand-in service function that records each real call."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.answer(*args, **kwargs)


# ---------------------------------------------------------------- per person

def test_two_volunteers_never_see_each_others_cached_pickups(monkeypatch):
    fake = Counter(lambda volunteer_id: [[volunteer_id, f"food for {volunteer_id}"]])
    monkeypatch.setattr(backend, "get_volunteer_pickups", fake)

    first = backend.get_volunteer_pickups_from_api(1)
    second = backend.get_volunteer_pickups_from_api(2)
    again = backend.get_volunteer_pickups_from_api(1)

    assert first == {"pickups": [[1, "food for 1"]]}
    assert second == {"pickups": [[2, "food for 2"]]}
    assert again == first                      # volunteer 1's own copy
    assert len(fake.calls) == 2                # third call came from cache


def test_two_organizations_never_see_each_others_cached_requests(monkeypatch):
    fake = Counter(lambda organization_id=None, volunteer_id=None:
                   [[organization_id, volunteer_id]])
    monkeypatch.setattr(backend, "get_all_pickup_requests", fake)

    assert backend.get_pickup_requests_from_api(organization_id=10) == \
        {"pickups": [[10, None]]}
    assert backend.get_pickup_requests_from_api(organization_id=20) == \
        {"pickups": [[20, None]]}
    # The admin view (no organization) is a separate cached copy too.
    assert backend.get_pickup_requests_from_api() == {"pickups": [[None, None]]}
    assert backend.get_pickup_requests_from_api(volunteer_id=10) == \
        {"pickups": [[None, 10]]}
    assert backend.get_pickup_requests_from_api(organization_id=10) == \
        {"pickups": [[10, None]]}
    assert len(fake.calls) == 4


def test_two_donors_never_see_each_others_cached_donations(monkeypatch):
    fake = Counter(lambda restaurant_id, limit: [[restaurant_id]])
    monkeypatch.setattr(backend, "get_donations_for_restaurant", fake)

    assert backend.get_my_donations_from_api(1) == {"donations": [[1]]}
    assert backend.get_my_donations_from_api(2) == {"donations": [[2]]}


def test_who_am_i_is_cached_per_email(monkeypatch):
    fake = Counter(lambda email: {"email": email, "status": "ACTIVE"})
    monkeypatch.setattr(user_service, "get_user", fake)

    assert backend.get_user("a@example.com")["email"] == "a@example.com"
    assert backend.get_user("b@example.com")["email"] == "b@example.com"
    assert backend.get_user("a@example.com")["email"] == "a@example.com"
    assert len(fake.calls) == 2


def test_switching_someone_off_takes_effect_within_30_seconds():
    assert backend.WHO_AM_I_SECONDS <= 30


# ---------------------------------------------------------------- writes clear

def _stub_all_writes(monkeypatch):
    ok = lambda *args, **kwargs: 1  # noqa: E731
    for name in ("add_restaurant", "add_food_donation", "add_organization",
                 "verify_organization", "reject_organization",
                 "request_pickup", "add_volunteer"):
        monkeypatch.setattr(backend, name, ok)
    monkeypatch.setattr(backend, "update_pickup_status",
                        lambda pickup_id, status: (pickup_id, status))
    monkeypatch.setattr(backend, "assign_volunteer",
                        lambda pickup_id, volunteer_id: {
                            "pickup_id": pickup_id,
                            "volunteer_id": volunteer_id})
    for name in ("ensure_admin", "request_access", "approve_user",
                 "set_user_status", "link_restaurant", "link_organization"):
        monkeypatch.setattr(user_service, name, ok)


WRITES = {
    "approve someone": lambda: backend.approve_user("a@example.com",
                                                    "VOLUNTEER"),
    "switch someone off": lambda: backend.set_user_status("a@example.com",
                                                          "DISABLED"),
    "ask for access": lambda: backend.request_access(
        "a@example.com", "A", "9", "Hyd", "DONOR"),
    "make admin": lambda: backend.ensure_admin("a@example.com", "A"),
    "link kitchen": lambda: backend.link_restaurant("a@example.com", 1),
    "link organization": lambda: backend.link_organization("a@example.com",
                                                           1),
    "verify organization": lambda: backend.verify_organization_from_api(1),
    "reject organization": lambda: backend.reject_organization_from_api(
        1, "reason"),
    "accept pickup": lambda: backend.update_pickup_status_from_api(
        1, "ACCEPTED"),
    "picked up / delivered": lambda: backend.update_pickup_status_from_api(
        1, "DELIVERED"),
    "assign volunteer": lambda: backend.assign_volunteer_to_pickup_from_api(
        1, 2),
    "request food": lambda: backend.create_pickup_from_api({
        "donation_id": 1, "organization_id": 1,
        "pickup_time": "2026-01-01T10:00:00"}),
    "share food": lambda: backend.create_donation_from_api({
        "restaurant_id": 1, "food_name": "Rice", "quantity": 1,
        "unit": "kg", "prepared_time": "2026-01-01T09:00:00",
        "expiry_time": "2026-01-01T11:00:00", "food_type": "VEGETARIAN",
        "packaging_status": "PACKED"}),
    "add restaurant": lambda: backend.create_restaurant_from_api(
        {"restaurant_name": "K"}),
    "add organization": lambda: backend.create_organization_from_api(
        {"organization_name": "O"}),
    "add volunteer": lambda: backend.create_volunteer_from_api(
        {"volunteer_name": "V", "phone": "9", "city": "Hyd"}),
}


@pytest.mark.parametrize("write", list(WRITES))
def test_every_write_clears_the_cache(monkeypatch, write):
    _stub_all_writes(monkeypatch)
    reads = Counter(lambda: [["fresh"]])
    monkeypatch.setattr(backend, "get_all_restaurants", reads)
    users = Counter(lambda email: {"email": email, "status": "ACTIVE"})
    monkeypatch.setattr(user_service, "get_user", users)

    backend.get_restaurants_from_api()
    backend.get_user("a@example.com")
    backend.get_restaurants_from_api()          # from the cache
    assert len(reads.calls) == 1

    WRITES[write]()

    backend.get_restaurants_from_api()          # must be read again
    backend.get_user("a@example.com")
    assert len(reads.calls) == 2, write
    assert len(users.calls) == 2, write


def test_errors_are_not_cached(monkeypatch):
    state = {"broken": True}

    def flaky():
        if state["broken"]:
            raise RuntimeError("database hiccup")
        return [["ok"]]

    monkeypatch.setattr(backend, "get_all_restaurants", flaky)
    assert "error" in backend.get_restaurants_from_api()
    state["broken"] = False
    assert backend.get_restaurants_from_api() == {"restaurants": [["ok"]]}


def test_admin_home_counts_are_one_call(monkeypatch):
    fake = Counter(lambda: {"food_available": 3, "urgent": 1})
    monkeypatch.setattr(backend, "get_admin_home_counts", fake)
    assert backend.get_admin_home_counts_from_api()["food_available"] == 3
    backend.get_admin_home_counts_from_api()
    assert len(fake.calls) == 1


# ---------------------------------------------------------------- pool checks

class FakeConnection:
    def __init__(self):
        self.closed = 0
        self.info = types.SimpleNamespace(transaction_status=0)  # IDLE
        self.executed = []
        self.rollbacks = 0

    def cursor(self):
        connection = self

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, sql):
                connection.executed.append(sql)

        return Cursor()

    def rollback(self):
        self.rollbacks += 1
        self.info.transaction_status = 0


class FakePool:
    def __init__(self):
        self.connection = FakeConnection()

    def getconn(self):
        return self.connection

    def putconn(self, connection, close=False):
        pass


def test_connection_is_checked_only_after_being_idle(monkeypatch):
    fake_pool = FakePool()
    clock = {"now": 1000.0}
    monkeypatch.setattr(database, "_get_pool", lambda: fake_pool)
    monkeypatch.setattr(database.time, "monotonic", lambda: clock["now"])
    database._last_used.clear()
    raw = fake_pool.connection

    database.get_connection().close()           # new to us: checked
    assert raw.executed == ["SELECT 1"]

    clock["now"] += 5
    database.get_connection().close()           # used 5 s ago: not checked
    assert raw.executed == ["SELECT 1"]

    clock["now"] += database.CHECK_IF_IDLE_SECONDS + 1
    database.get_connection().close()           # idle a while: checked
    assert raw.executed == ["SELECT 1", "SELECT 1"]
    database._last_used.clear()


def test_open_transaction_is_rolled_back_but_idle_one_is_not(monkeypatch):
    fake_pool = FakePool()
    monkeypatch.setattr(database, "_get_pool", lambda: fake_pool)
    database._last_used.clear()
    raw = fake_pool.connection

    connection = database.get_connection()
    rollbacks_after_check = raw.rollbacks
    connection.close()                          # nothing open: no rollback
    assert raw.rollbacks == rollbacks_after_check

    connection = database.get_connection()
    raw.info.transaction_status = 2             # a read left one open
    connection.close()
    assert raw.rollbacks == rollbacks_after_check + 1
    database._last_used.clear()
