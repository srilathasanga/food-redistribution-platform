from datetime import datetime, timedelta

from app.donation_service import add_food_donation
from app.pickup_service import request_pickup, update_pickup_status


print("======================================")
print("DONATION + PICKUP LIFECYCLE TEST")
print("======================================")

now = datetime.now()

prepared_time = now - timedelta(hours=1)
expiry_time = now + timedelta(hours=6)
pickup_time = now + timedelta(hours=2)


# Create a fresh donation
donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Fresh Lifecycle Test Meals",
    food_category="Cooked Meals",
    quantity=15,
    unit="kg",
    prepared_time=prepared_time,
    expiry_time=expiry_time,
    food_type="VEGETARIAN",
    packaging_status="PACKED",
    pickup_address="123 Main Road, Hyderabad"
)

print("\n1. Food donation created!")
print("Donation ID:", donation_id)


# Create pickup request
pickup_id = request_pickup(
    donation_id=donation_id,
    organization_id=1,
    pickup_time=pickup_time,
    pickup_address="123 Main Road, Hyderabad",
    notes="Test complete donation and pickup lifecycle."
)

print("\n2. Pickup request created!")
print("Pickup ID:", pickup_id)


# Step 1: REQUESTED -> ACCEPTED
result = update_pickup_status(
    pickup_id,
    "ACCEPTED"
)

print("\n3. Pickup accepted!")
print("Pickup ID:", result[0])
print("Status:", result[1])


# Step 2: ACCEPTED -> PICKED_UP
result = update_pickup_status(
    pickup_id,
    "PICKED_UP"
)

print("\n4. Food picked up!")
print("Pickup ID:", result[0])
print("Status:", result[1])


# Step 3: PICKED_UP -> DELIVERED
result = update_pickup_status(
    pickup_id,
    "DELIVERED"
)

print("\n5. Food delivered!")
print("Pickup ID:", result[0])
print("Status:", result[1])


print("\n======================================")
print("LIFECYCLE TEST COMPLETED")
print("======================================")