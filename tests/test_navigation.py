"""Each role sees only its own pages. Needs no database."""

import pytest

from app.navigation import MENU, PAGES, pages_for, title_for

pytestmark = pytest.mark.no_database

ADMIN_ONLY = {"admin", "user-access", "restaurants", "organizations",
              "volunteers"}


def test_every_role_starts_at_home_and_pages_exist():
    for role in ("ADMIN", "DONOR", "ORGANIZATION", "VOLUNTEER"):
        pages = pages_for(role)
        assert pages[0] == "home"
        assert len(pages) == len(set(pages))
        assert set(pages) <= set(PAGES)


def test_admin_only_pages_are_hidden_from_everyone_else():
    for role in ("DONOR", "ORGANIZATION", "VOLUNTEER"):
        assert not ADMIN_ONLY & set(pages_for(role)), role


def test_each_role_gets_exactly_its_pages():
    assert pages_for("DONOR") == ["home", "my-restaurant", "donations"]
    assert pages_for("ORGANIZATION") == [
        "home", "my-organization", "available-food", "pickups",
    ]
    assert pages_for("VOLUNTEER") == ["home", "pickups"]
    assert set(pages_for("ADMIN")) == set(PAGES) - {
        "my-restaurant", "my-organization", "available-food",
    }


def test_unknown_role_sees_nothing():
    assert pages_for("SOMEONE") == []
    assert "SOMEONE" not in MENU


def test_friendly_titles():
    assert title_for("VOLUNTEER", "pickups") == "My pickups"
    assert title_for("ADMIN", "pickups") == "Pickup requests"
