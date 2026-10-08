from app.restaurant_service import add_restaurant, get_all_restaurants


# Add a test restaurant
restaurant_id = add_restaurant(
    "Sunrise Restaurant",
    "Ravi Kumar",
    "9999999999",
    "sunrise@example.com",
    "10 Main Road",
    "Hyderabad"
)

print("New restaurant created!")
print("Restaurant ID:", restaurant_id)


# Get all restaurants
restaurants = get_all_restaurants()

print("\nAll restaurants:")

for restaurant in restaurants:
    print(restaurant)