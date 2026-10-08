from app.organization_service import (
    add_organization,
    get_verified_organizations
)


organization_id = add_organization(
    organization_name="Food Care Trust",
    contact_person="Meena Reddy",
    phone="9000000000",
    email="foodcare@example.com",
    address="25 Community Road",
    city="Hyderabad",
    organization_type="NGO"
)

print("Organization created!")
print("Organization ID:", organization_id)


# For testing, we will verify this organization directly in the database later.

organizations = get_verified_organizations()

print("\nVerified organizations:")

for organization in organizations:
    print(organization)