
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.restaurant_service import (
    add_restaurant,
    get_all_restaurants
)

from app.food_risk_service import get_food_risk_analysis

from app.donation_service import (
    add_food_donation,
    get_available_donations,
    get_donation_summary
)

from app.organization_service import (
    add_organization,
    get_verified_organizations,
    get_pending_organizations,
    verify_organization,
    reject_organization,
    get_organization_summary
)

from app.pickup_service import (
    request_pickup,
    get_all_pickup_requests,
    update_pickup_status,
    assign_volunteer,
    get_pickup_summary
)

from app.volunteer_service import (
    add_volunteer,
    get_all_volunteers,
    get_volunteer_summary
)



app = FastAPI(
    title="Food Redistribution API",
    description="API for the Food Redistribution Platform",
    version="1.0.0"
)


# =========================================================
# REQUEST MODELS
# =========================================================

class RestaurantCreate(BaseModel):
    restaurant_name: str
    contact_person: str
    phone: str
    email: str
    address: str
    city: str


class DonationCreate(BaseModel):
    restaurant_id: int
    food_name: str
    food_category: str
    quantity: float
    unit: str
    prepared_time: datetime
    expiry_time: datetime
    food_type: str
    packaging_status: str
    pickup_address: str

### Organization creation###


class OrganizationCreate(BaseModel):
    organization_name: str
    contact_person: str
    phone: str
    email: str
    address: str
    city: str
    organization_type: str


class OrganizationReject(BaseModel):
    rejection_reason: str
###pickup create requests####
class PickupCreate(BaseModel):
    donation_id: int
    organization_id: int
    pickup_time: datetime
    pickup_address: str
    notes: str | None = None
##Pickup status##
class PickupStatusUpdate(BaseModel):
    new_status: str
### volunteer#
class VolunteerCreate(BaseModel):
    volunteer_name: str
    phone: str
    email: str
    address: str
    city: str
##Volunteer Assignement##
class VolunteerAssignment(BaseModel):
    volunteer_id: int
# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Food Redistribution API is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# RESTAURANT APIs
# =========================================================

@app.post("/restaurants")
def create_restaurant(restaurant: RestaurantCreate):

    restaurant_id = add_restaurant(
        restaurant.restaurant_name,
        restaurant.contact_person,
        restaurant.phone,
        restaurant.email,
        restaurant.address,
        restaurant.city
    )

    return {
        "message": "Restaurant created successfully",
        "restaurant_id": restaurant_id
    }


@app.get("/restaurants")
def get_restaurants():

    restaurants = get_all_restaurants()

    return {
        "restaurants": restaurants
    }


# =========================================================
# FOOD DONATION APIs
# =========================================================

# =========================================================
# FOOD DONATION APIs
# =========================================================

@app.post("/donations")
def create_donation(donation: DonationCreate):

    try:
        donation_id = add_food_donation(
            donation.restaurant_id,
            donation.food_name,
            donation.food_category,
            donation.quantity,
            donation.unit,
            donation.prepared_time,
            donation.expiry_time,
            donation.food_type,
            donation.packaging_status,
            donation.pickup_address
        )

        return {
            "message": "Food donation created successfully",
            "donation_id": donation_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.get("/donations/available")
def get_available_food_donations():

    donations = get_available_donations()

    return {
        "donations": donations
    }
#donation summary API##

@app.get("/donations/summary")
def donation_summary():

    summary = get_donation_summary()

    return {
        "summary": summary
    }

@app.get("/donations/risk-analysis")
def food_risk_analysis():

    results = get_food_risk_analysis()

    return {
        "count": len(results),
        "risk_analysis": results
    }



### Organization###


# =========================================================
# ORGANIZATION APIs
# =========================================================

@app.post("/organizations")
def create_organization(organization: OrganizationCreate):

    organization_id = add_organization(
        organization.organization_name,
        organization.contact_person,
        organization.phone,
        organization.email,
        organization.address,
        organization.city,
        organization.organization_type
    )

    return {
        "message": "Organization created successfully",
        "organization_id": organization_id
    }


@app.get("/organizations/verified")
def get_verified_orgs():

    organizations = get_verified_organizations()

    return {
        "organizations": organizations
    }


@app.get("/organizations/pending")
def get_pending_orgs():

    organizations = get_pending_organizations()

    return {
        "organizations": organizations
    }
## Org summary API##

@app.get("/organizations/summary")
def organization_summary():

    summary = get_organization_summary()

    return {
        "summary": summary
    }




@app.put("/organizations/{organization_id}/verify")
def verify_org(organization_id: int):

    try:
        verified_id = verify_organization(organization_id)

        return {
            "message": "Organization verified successfully",
            "organization_id": verified_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.put("/organizations/{organization_id}/reject")
def reject_org(
    organization_id: int,
    request: OrganizationReject
):

    try:
        rejected_id = reject_organization(
            organization_id,
            request.rejection_reason
        )

        return {
            "message": "Organization rejected successfully",
            "organization_id": rejected_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
### PIckup API###
@app.post("/pickups")
def create_pickup(pickup: PickupCreate):
    try:
        pickup_id = request_pickup(
            pickup.donation_id,
            pickup.organization_id,
            pickup.pickup_time,
            pickup.pickup_address,
            pickup.notes
        )

        return {
            "message": "Pickup request created successfully",
            "pickup_id": pickup_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.get("/pickups")
def get_pickups():
    pickups = get_all_pickup_requests()

    return {
        "pickups": pickups
    }
##pickup summary##

@app.get("/pickups/summary")
def pickup_summary():

    summary = get_pickup_summary()

    return {
        "summary": summary
    }


## get pickups##
@app.put("/pickups/{pickup_id}/status")
def change_pickup_status(
    pickup_id: int,
    request: PickupStatusUpdate
):
    try:
        updated_pickup_id, new_status = update_pickup_status(
            pickup_id,
            request.new_status
        )

        return {
            "message": "Pickup status updated successfully",
            "pickup_id": updated_pickup_id,
            "new_status": new_status
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
@app.post("/volunteers")
def create_volunteer(volunteer: VolunteerCreate):

    volunteer_id = add_volunteer(
        volunteer_name=volunteer.volunteer_name,
        phone=volunteer.phone,
        email=volunteer.email,
        address=volunteer.address,
        city=volunteer.city
    )

    return {
        "message": "Volunteer created successfully",
        "volunteer_id": volunteer_id
    }
## get volunteers
@app.get("/volunteers")
def get_volunteers():

    volunteers = get_all_volunteers()

    return {
        "volunteers": volunteers
    }

@app.get("/volunteers/summary")
def volunteer_summary():

    summary = get_volunteer_summary()

    return {
        "summary": summary
    }



##Assign volunteer to pickup###
@app.put("/pickups/{pickup_id}/volunteer")
def assign_volunteer_to_pickup(
    pickup_id: int,
    assignment: VolunteerAssignment
):

    result = assign_volunteer(
        pickup_id,
        assignment.volunteer_id
    )

    return {
        "message": "Volunteer assigned successfully",
        "pickup_id": result["pickup_id"],
        "volunteer_id": result["volunteer_id"]
    }