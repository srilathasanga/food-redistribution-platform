from app.donation_service import add_food_donation
from app.pickup_service import (
    request_pickup,
    get_all_pickup_requests
)


# Create a fresh donation for pickup testing
donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Fresh Pickup Test Meals",
    food_category="Cooked Meals",
    quantity=10,
    unit="kg",
    prepared_time="2026-10-08 12:00:00",
    expiry_time="2026-10-08 18:00:00",
    food_type="VEGETARIAN",
    packaging_status="PACKED",
    pickup_address="123 Main Road, Hyderabad"
)

print("Food donation created!")
print("Donation ID:", donation_id)


# Request pickup
pickup_id = request_pickup(
    donation_id=donation_id,
    organization_id=1,
    pickup_time="2026-10-08 14:00:00",
    pickup_address="123 Main Road, Hyderabad",
    notes="Please collect the food within the safe consumption window."
)

print("\nPickup request created!")
print("Pickup ID:", pickup_id)


# Display all pickup requests
pickup_requests = get_all_pickup_requests()

print("\nAll pickup requests:")

for pickup in pickup_requests:
    print(pickup)