from app.volunteer_service import (
    add_volunteer,
    get_all_volunteers
)


print("======================================")
print("VOLUNTEER SERVICE TEST")
print("======================================")


volunteer_id = add_volunteer(
    volunteer_name="Ravi Kumar",
    phone="9876501234",
    email="ravi.volunteer@example.com",
    address="25 Community Road",
    city="Hyderabad"
)

print("Volunteer created!")
print("Volunteer ID:", volunteer_id)


print()
print("All volunteers:")

volunteers = get_all_volunteers()

for volunteer in volunteers:
    print(volunteer)