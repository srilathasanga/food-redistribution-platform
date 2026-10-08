from app.pickup_service import update_pickup_status


# Pickup #6 is currently REQUESTED
pickup_id = 6

print("Starting pickup status workflow...")
print("Pickup ID:", pickup_id)


# REQUESTED -> ACCEPTED
result = update_pickup_status(
    pickup_id,
    "ACCEPTED"
)

print("\n1. Pickup accepted")
print("Pickup ID:", result[0])
print("New Status:", result[1])


# ACCEPTED -> PICKED_UP
result = update_pickup_status(
    pickup_id,
    "PICKED_UP"
)

print("\n2. Food picked up")
print("Pickup ID:", result[0])
print("New Status:", result[1])


# PICKED_UP -> DELIVERED
result = update_pickup_status(
    pickup_id,
    "DELIVERED"
)

print("\n3. Food delivered")
print("Pickup ID:", result[0])
print("New Status:", result[1])


print("\nPickup status workflow completed successfully!")