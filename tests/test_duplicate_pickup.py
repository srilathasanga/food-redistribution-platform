from app.donation_service import add_food_donation
from app.pickup_service import request_pickup

print("======================================")
print("DUPLICATE PICKUP TEST")
print("======================================")

# Create a fresh donation
donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Fresh Duplicate Test Meals",
    food_category="Cooked Meals",
    quantity=10,
    unit="kg",
    prepared_time="2026-09-17 12:00:00",
    expiry_time="2026-09-17 20:00:00",
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
    pickup_time="2026-09-17 15:00:00",
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
        pickup_time="2026-09-17 15:30:00",
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