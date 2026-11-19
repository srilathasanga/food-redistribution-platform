"""Functions the Streamlit UI calls.

These used to send HTTP requests to the FastAPI server on Render. They
now call the service functions directly, so there is no second server to
wake up and no 5-second timeout. Each one returns the same shape the API
returned (dates as ISO strings, numbers as floats), or {"error": "..."}.

Speed: each database round trip costs about 0.26 s from India to Neon in
the US, and Streamlit re-runs the whole page on every click. So read
results are kept for a short time (st.cache_data):

- Results that depend on a person (their donations, their pickups, their
  restaurant or organization, the "who am I" lookup) take that person's
  id as an argument, so each person has their own cached copy.
- Errors are never cached (the cached functions raise; _safe() turns the
  error into a message outside the cache).
- EVERY write clears ALL cached results at once (clear_caches), so nobody
  sees old data after a change. That includes approvals, verify/reject,
  accept/assign and status changes.

The FastAPI app in app/main.py still works for learning or for a future
mobile app; it is no longer needed to run the website.
"""

import functools
import json
import logging
from datetime import date, datetime, time
from decimal import Decimal

import streamlit as st

from app import user_service
from app.dashboard_service import (
    get_admin_home_counts,
    get_impact_summary,
    get_urgent_food,
)
from app.donation_service import (
    add_food_donation,
    get_available_donations,
    get_donation_summary,
    get_donations_for_restaurant,
    get_requestable_donations,
)
from app.food_risk_service import get_food_risk_analysis
from app.organization_service import (
    add_organization,
    get_organization_summary,
    get_pending_organizations,
    get_verified_organizations,
    reject_organization,
    verify_organization,
)
from app.pickup_service import (
    assign_volunteer,
    get_all_pickup_requests,
    get_pickup_summary,
    get_volunteer_pickups,
    request_pickup,
    update_pickup_status,
)
from app.restaurant_service import add_restaurant, get_all_restaurants
from app.volunteer_service import (
    add_volunteer,
    get_all_volunteers,
    get_volunteer_summary,
)

logger = logging.getLogger(__name__)

# How long read results are kept.
CACHE_SECONDS = 30
# "Who am I" (sign-in check): switching someone off must take effect
# within 30 seconds, even without a cache clear.
WHO_AM_I_SECONDS = 20


def clear_caches():
    """Forget every cached read result. Called after every write."""
    st.cache_data.clear()


def _cached(ttl=CACHE_SECONDS):
    return st.cache_data(ttl=ttl, show_spinner=False)


def _json_default(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot serialise {type(value).__name__}")


def _plain(value):
    """Same conversion FastAPI did: tuples -> lists, dates -> strings."""
    return json.loads(json.dumps(value, default=_json_default))


def _safe(action):
    try:
        return _plain(action())
    except ValueError as error:
        # Business-rule messages, safe to show to the user.
        return {"error": str(error)}
    except Exception:
        logger.exception("Unexpected error")
        return {
            "error": "Something went wrong while talking to the database. "
            "Please try again in a moment."
        }


def _write(action):
    """Run a write; on success forget all cached reads."""
    result = _safe(action)
    if "error" not in result:
        clear_caches()
    return result


def _clears_caches(name):
    """A write from user_service that always clears the caches afterwards
    (even if it fails part-way). Looked up by name at call time."""
    @functools.wraps(getattr(user_service, name))
    def wrapper(*args, **kwargs):
        try:
            return getattr(user_service, name)(*args, **kwargs)
        finally:
            clear_caches()
    return wrapper


def _parse_time(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


# ---------------------------------------------------------------- people
# Reads (cached per email / id) and writes (clear the caches).

@_cached(ttl=WHO_AM_I_SECONDS)
def get_user(email):
    return user_service.get_user(email)


@_cached()
def get_restaurant(restaurant_id):
    return user_service.get_restaurant(restaurant_id)


@_cached()
def get_organization(organization_id):
    return user_service.get_organization(organization_id)


@_cached()
def list_users(status=None):
    return user_service.list_users(status=status)


ensure_admin = _clears_caches("ensure_admin")
request_access = _clears_caches("request_access")
approve_user = _clears_caches("approve_user")
set_user_status = _clears_caches("set_user_status")
link_restaurant = _clears_caches("link_restaurant")
link_organization = _clears_caches("link_organization")
# record_login only updates "last signed in"; it does not clear caches.
record_login = user_service.record_login


# ---------------------------------------------------------------- restaurants

@_cached()
def _restaurants():
    return _plain(get_all_restaurants())


def get_restaurants_from_api():
    return _safe(lambda: {"restaurants": _restaurants()})


def create_restaurant_from_api(restaurant_data):
    def action():
        restaurant_id = add_restaurant(
            restaurant_data["restaurant_name"],
            restaurant_data.get("contact_person"),
            restaurant_data.get("phone"),
            restaurant_data.get("email"),
            restaurant_data.get("address"),
            restaurant_data.get("city"),
        )
        return {
            "message": "Restaurant created successfully",
            "restaurant_id": restaurant_id,
        }

    return _write(action)


# ------------------------------------------------------------------ donations

def create_donation_from_api(donation_data):
    def action():
        donation_id = add_food_donation(
            donation_data["restaurant_id"],
            donation_data["food_name"],
            donation_data.get("food_category"),
            donation_data["quantity"],
            donation_data["unit"],
            _parse_time(donation_data["prepared_time"]),
            _parse_time(donation_data["expiry_time"]),
            donation_data["food_type"],
            donation_data["packaging_status"],
            donation_data.get("pickup_address"),
        )
        return {
            "message": "Food donation created successfully",
            "donation_id": donation_id,
        }

    return _write(action)


@_cached()
def _available_donations():
    return _plain(get_available_donations())


def get_available_donations_from_api():
    return _safe(lambda: {"donations": _available_donations()})


@_cached()
def _my_donations(restaurant_id, limit):
    # Cached per restaurant: the id is an argument.
    return _plain(get_donations_for_restaurant(restaurant_id, limit))


def get_my_donations_from_api(restaurant_id, limit=10):
    return _safe(lambda: {"donations": _my_donations(restaurant_id, limit)})


@_cached()
def _requestable_donations():
    return _plain(get_requestable_donations())


def get_requestable_donations_from_api():
    return _safe(lambda: {"donations": _requestable_donations()})


@_cached()
def _donation_summary():
    return _plain(get_donation_summary())


def get_donation_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(_donation_summary)


@_cached()
def _food_risk():
    return _plain(get_food_risk_analysis())


def get_food_risk_analysis_from_api():
    def action():
        results = _food_risk()
        return {"count": len(results), "risk_analysis": results}

    return _safe(action)


# -------------------------------------------------------------- home numbers

@_cached()
def _admin_home_counts():
    return _plain(get_admin_home_counts())


def get_admin_home_counts_from_api():
    """All of the admin Home numbers in one database query."""
    return _safe(_admin_home_counts)


@_cached()
def _impact(month_start):
    return _plain(get_impact_summary(month_start))


def get_impact_from_api(month_start):
    """Ministry-wide totals for the Home impact strip (not per person)."""
    return _safe(lambda: _impact(month_start))


@_cached()
def _urgent_food():
    return _plain(get_urgent_food())


def get_urgent_food_from_api():
    return _safe(lambda: {"donations": _urgent_food()})


# -------------------------------------------------------------- organizations

def create_organization_from_api(organization_data):
    def action():
        organization_id = add_organization(
            organization_data["organization_name"],
            organization_data.get("contact_person"),
            organization_data.get("phone"),
            organization_data.get("email"),
            organization_data.get("address"),
            organization_data.get("city"),
            organization_data.get("organization_type"),
        )
        return {
            "message": "Organization created successfully",
            "organization_id": organization_id,
        }

    return _write(action)


@_cached()
def _verified_organizations():
    return _plain(get_verified_organizations())


def get_verified_organizations_from_api():
    return _safe(lambda: {"organizations": _verified_organizations()})


@_cached()
def _pending_organizations():
    return _plain(get_pending_organizations())


def get_pending_organizations_from_api():
    return _safe(lambda: {"organizations": _pending_organizations()})


@_cached()
def _organization_summary():
    return _plain(get_organization_summary())


def get_organization_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(_organization_summary)


def verify_organization_from_api(organization_id):
    def action():
        return {
            "message": "Organization verified successfully",
            "organization_id": verify_organization(organization_id),
        }

    return _write(action)


def reject_organization_from_api(organization_id, rejection_reason):
    def action():
        return {
            "message": "Organization rejected successfully",
            "organization_id": reject_organization(
                organization_id, rejection_reason
            ),
        }

    return _write(action)


# -------------------------------------------------------------------- pickups

def create_pickup_from_api(pickup_data):
    def action():
        pickup_id = request_pickup(
            pickup_data["donation_id"],
            pickup_data["organization_id"],
            _parse_time(pickup_data["pickup_time"]),
            pickup_data.get("pickup_address"),
            pickup_data.get("notes"),
        )
        return {
            "message": "Pickup request created successfully",
            "pickup_id": pickup_id,
        }

    return _write(action)


@_cached()
def _pickup_requests(organization_id, volunteer_id):
    # Cached per organization / per volunteer: they are arguments.
    return _plain(get_all_pickup_requests(
        organization_id=organization_id, volunteer_id=volunteer_id
    ))


def get_pickup_requests_from_api(organization_id=None, volunteer_id=None):
    return _safe(
        lambda: {"pickups": _pickup_requests(organization_id, volunteer_id)}
    )


@_cached()
def _volunteer_pickups(volunteer_id):
    # Cached per volunteer: the id is the argument.
    return _plain(get_volunteer_pickups(volunteer_id))


def get_volunteer_pickups_from_api(volunteer_id):
    # Delivery address and contact only for this volunteer's ACTIVE
    # pickups; the query itself enforces this.
    return _safe(lambda: {"pickups": _volunteer_pickups(volunteer_id)})


@_cached()
def _pickup_summary():
    return _plain(get_pickup_summary())


def get_pickup_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(_pickup_summary)


def update_pickup_status_from_api(pickup_id, new_status):
    def action():
        updated_id, status = update_pickup_status(pickup_id, new_status)
        return {
            "message": "Pickup status updated successfully",
            "pickup_id": updated_id,
            "new_status": status,
        }

    return _write(action)


def assign_volunteer_to_pickup_from_api(pickup_id, volunteer_id):
    def action():
        result = assign_volunteer(pickup_id, volunteer_id)
        return {
            "message": "Volunteer assigned successfully",
            "pickup_id": result["pickup_id"],
            "volunteer_id": result["volunteer_id"],
        }

    return _write(action)


# ----------------------------------------------------------------- volunteers

def create_volunteer_from_api(volunteer_data):
    def action():
        volunteer_id = add_volunteer(
            volunteer_name=volunteer_data["volunteer_name"],
            phone=volunteer_data["phone"],
            email=volunteer_data.get("email"),
            address=volunteer_data.get("address"),
            city=volunteer_data["city"],
        )
        return {
            "message": "Volunteer created successfully",
            "volunteer_id": volunteer_id,
        }

    return _write(action)


@_cached()
def _volunteers():
    return _plain(get_all_volunteers())


def get_volunteers_from_api():
    return _safe(lambda: {"volunteers": _volunteers()})


@_cached()
def _volunteer_summary():
    return _plain(get_volunteer_summary())


def get_volunteer_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(_volunteer_summary)
