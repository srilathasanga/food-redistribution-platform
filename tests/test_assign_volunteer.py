from app.pickup_service import assign_volunteer


print("======================================")
print("ASSIGN VOLUNTEER TEST")
print("======================================")


pickup_id = 15
volunteer_id = 3

result = assign_volunteer(
    pickup_id,
    volunteer_id
)

print("Volunteer assigned successfully!")
print("Pickup ID:", result["pickup_id"])
print("Volunteer ID:", result["volunteer_id"])