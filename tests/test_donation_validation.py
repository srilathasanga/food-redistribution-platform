from app.donation_service import add_food_donation

print("======================================")
print("DONATION VALIDATION TEST")
print("======================================")


def test_case(title, **kwargs):
    print(f"\n--- {title} ---")

    try:
        donation_id = add_food_donation(**kwargs)
        print("❌ ERROR: Invalid donation was accepted!")
        print("Donation ID:", donation_id)

    except ValueError as e:
        print("✅ Rejected correctly!")
        print("Reason:", e)


common_data = {
    "restaurant_id": 1,
    "food_category": "Cooked Meals",
    "quantity": 10,
    "unit": "kg",
    "prepared_time": "2026-09-17 12:00:00",
    "expiry_time": "2026-09-17 18:00:00",
    "food_type": "VEGETARIAN",
    "packaging_status": "PACKED",
    "pickup_address": "123 Main Road, Hyderabad"
}


# 1. Empty food name
test_case(
    "Empty food name",
    food_name="",
    **common_data
)


# 2. Zero quantity
invalid_quantity = common_data.copy()
invalid_quantity["quantity"] = 0

test_case(
    "Zero quantity",
    food_name="Test Food",
    **invalid_quantity
)


# 3. Negative quantity
invalid_quantity = common_data.copy()
invalid_quantity["quantity"] = -5

test_case(
    "Negative quantity",
    food_name="Test Food",
    **invalid_quantity
)


# 4. Expiry before prepared time
invalid_time = common_data.copy()
invalid_time["expiry_time"] = "2026-09-17 10:00:00"

test_case(
    "Expiry before prepared time",
    food_name="Test Food",
    **invalid_time
)


# 5. Invalid food type
invalid_food_type = common_data.copy()
invalid_food_type["food_type"] = "UNKNOWN"

test_case(
    "Invalid food type",
    food_name="Test Food",
    **invalid_food_type
)


# 6. Invalid packaging status
invalid_packaging = common_data.copy()
invalid_packaging["packaging_status"] = "DAMAGED"

test_case(
    "Invalid packaging status",
    food_name="Test Food",
    **invalid_packaging
)


# 7. Valid donation
print("\n--- Valid donation ---")

try:
    donation_id = add_food_donation(
        food_name="Fresh Validation Test Meals",
        **common_data
    )

    print("✅ Valid donation accepted!")
    print("Donation ID:", donation_id)

except Exception as e:
    print("❌ ERROR: Valid donation was rejected!")
    print("Reason:", e)


print("\n======================================")
print("DONATION VALIDATION TEST COMPLETED")
print("======================================")