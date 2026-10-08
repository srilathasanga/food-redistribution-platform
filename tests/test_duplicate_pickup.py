from datetime import datetime, timedelta

from app.donation_service import add_food_donation
from app.pickup_service import request_pickup

print("======================================")
print("DUPLICATE PICKUP TEST")
print("======================================")


now = datetime.now()

prepared_time = now - timedelta(hours=1)
expiry_time = now + timedelta(hours=6)
first_pickup_time = now + timedelta(hours=2)
second_pickup_time = now + timedelta(hours=2, minutes=30)


# Create a fresh donation
donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Fresh Duplicate Test Meals",
    food_category="Cooked Meals",
    quantity=10,
    unit="kg",
    prepared_time=prepared_time,
    expiry_time=expiry_time,
    food_type="VEGETARIAN",
    packaging_status="PACKED",
    pickup_address="123 Main Road, Hyderabad"
)
print("\n1. Fresh donation created!")
print("Donation ID:", donation_id)

# First pickup request
pickup_id = request_pickup(
    donation_id=donation_id,
    organization_id=1,
    pickup_time=first_pickup_time,
    pickup_address="123 Main Road, Hyderabad",
    notes="First pickup request."
)

print("\n2. First pickup request created!")
print("Pickup ID:", pickup_id)

# Second pickup request for the same donation
print("\n3. Attempting duplicate pickup request...")

try:
    request_pickup(
        donation_id=donation_id,
        organization_id=1,
        pickup_time=first_pickup_time,
        pickup_address="123 Main Road, Hyderabad",
        notes="Duplicate pickup request."
    )

    print("ERROR: Duplicate pickup request was allowed!")

except ValueError as e:
    print("\n4. Duplicate pickup request rejected!")
    print("Reason:", e)

print("\n======================================")
print("DUPLICATE PICKUP TEST COMPLETED")
print("======================================")