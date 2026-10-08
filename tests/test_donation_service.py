from app.donation_service import add_food_donation, get_available_donations


# Add a test food donation
donation_id = add_food_donation(
    restaurant_id=1,
    food_name="Vegetable Biryani",
    food_category="Cooked Meals",
    quantity=15,
    unit="kg",
    prepared_time="2026-09-16 18:00:00",
    expiry_time="2026-09-17 00:00:00",
    food_type="VEGETARIAN",
    packaging_status="PACKED",
    pickup_address="123 Main Road, Hyderabad"
)

print("Food donation created!")
print("Donation ID:", donation_id)


# Display available donations
donations = get_available_donations()

print("\nAvailable food donations:")

for donation in donations:
    print(donation)