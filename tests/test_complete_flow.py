from app.donation_service import add_food_donation
from app.pickup_service import request_pickup, update_pickup_status


print("======================================")
print("FOOD REDISTRIBUTION END-TO-END TEST")
print("======================================")


# -------------------------------------------------
# STEP 1: Create a new food donation
# -------------------------------------------------

donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Fresh Vegetable Rice",
    food_category="Cooked Meals",
    quantity=20,
    unit="kg",
    prepared_time="2026-09-17 10:00:00",
    expiry_time="2026-09-17 18:00:00",
    food_type="VEGETARIAN",
    packaging_status="PACKED",
    pickup_address="123 Main Road, Hyderabad"
)

print("\n1. Food donation created")
print("Donation ID:", donation_id)


# -------------------------------------------------
# STEP 2: Organization requests pickup
# -------------------------------------------------

pickup_id = request_pickup(
    donation_id=donation_id,
    organization_id=1,
    pickup_time="2026-09-17 13:00:00",
    pickup_address="123 Main Road, Hyderabad",
    notes="End-to-end platform test."
)

print("\n2. Pickup request created")
print("Pickup ID:", pickup_id)


# -------------------------------------------------
# STEP 3: ACCEPTED
# -------------------------------------------------

result = update_pickup_status(
    pickup_id,
    "ACCEPTED"
)

print("\n3. Pickup accepted")
print("Status:", result[1])


# -------------------------------------------------
# STEP 4: PICKED_UP
# -------------------------------------------------

result = update_pickup_status(
    pickup_id,
    "PICKED_UP"
)

print("\n4. Food picked up")
print("Status:", result[1])


# -------------------------------------------------
# STEP 5: DELIVERED
# -------------------------------------------------

result = update_pickup_status(
    pickup_id,
    "DELIVERED"
)

print("\n5. Food delivered")
print("Status:", result[1])


print("\n======================================")
print("END-TO-END TEST COMPLETED")
print("======================================")