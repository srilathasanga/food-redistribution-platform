"""Functions the Streamlit UI calls.

These used to send HTTP requests to the FastAPI server on Render. They
now call the service functions directly, so there is no second server to
wake up and no 5-second timeout. Each one returns the same shape the API
returned (dates as ISO strings, numbers as floats), or {"error": "..."}.

The FastAPI app in app/main.py still works for learning or for a future
mobile app; it is no longer needed to run the website.
"""

import json
import logging
from datetime import date, datetime, time
from decimal import Decimal

from app.donation_service import (
    add_food_donation,
    get_available_donations,
    get_donation_summary,
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


def _parse_time(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


# ---------------------------------------------------------------- restaurants

def get_restaurants_from_api():
    return _safe(lambda: {"restaurants": get_all_restaurants()})


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

    return _safe(action)


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

    return _safe(action)


def get_available_donations_from_api():
    return _safe(lambda: {"donations": get_available_donations()})


def get_donation_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(get_donation_summary)


def get_food_risk_analysis_from_api():
    def action():
        results = get_food_risk_analysis()
        return {"count": len(results), "risk_analysis": results}

    return _safe(action)


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

    return _safe(action)


def get_verified_organizations_from_api():
    return _safe(lambda: {"organizations": get_verified_organizations()})


def get_pending_organizations_from_api():
    return _safe(lambda: {"organizations": get_pending_organizations()})


def get_organization_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(get_organization_summary)


def verify_organization_from_api(organization_id):
    def action():
        return {
            "message": "Organization verified successfully",
            "organization_id": verify_organization(organization_id),
        }

    return _safe(action)


def reject_organization_from_api(organization_id, rejection_reason):
    def action():
        return {
            "message": "Organization rejected successfully",
            "organization_id": reject_organization(
                organization_id, rejection_reason
            ),
        }

    return _safe(action)


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

    return _safe(action)


def get_pickup_requests_from_api(organization_id=None, volunteer_id=None):
    return _safe(
        lambda: {
            "pickups": get_all_pickup_requests(
                organization_id=organization_id, volunteer_id=volunteer_id
            )
        }
    )


def get_pickup_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(get_pickup_summary)


def update_pickup_status_from_api(pickup_id, new_status):
    def action():
        updated_id, status = update_pickup_status(pickup_id, new_status)
        return {
            "message": "Pickup status updated successfully",
            "pickup_id": updated_id,
            "new_status": status,
        }

    return _safe(action)


def assign_volunteer_to_pickup_from_api(pickup_id, volunteer_id):
    def action():
        result = assign_volunteer(pickup_id, volunteer_id)
        return {
            "message": "Volunteer assigned successfully",
            "pickup_id": result["pickup_id"],
            "volunteer_id": result["volunteer_id"],
        }

    return _safe(action)


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

    return _safe(action)


def get_volunteers_from_api():
    return _safe(lambda: {"volunteers": get_all_volunteers()})


def get_volunteer_summary_from_api():
    # The UI reads the summary fields directly.
    return _safe(get_volunteer_summary)
