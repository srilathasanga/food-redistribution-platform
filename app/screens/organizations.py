"""Organizations: My organization and Organizations (admin)."""

import streamlit as st

from app import ui
from app.backend import (
    create_organization_from_api,
    get_verified_organizations_from_api,
)
from app.user_service import (
    link_organization,
)

flash_success = ui.flash_success


def my_organization_page(ctx):
    user = ctx.user
    my_organization = ctx.my_organization

    st.header("🏢 My Organization")

    if my_organization:
        st.write(f"**Name:** {my_organization[1]}")
        st.write(f"**Type:** {my_organization[7]}")
        st.write(f"**Contact person:** {my_organization[2]}")
        st.write(f"**Phone:** {my_organization[3]}")
        st.write(f"**Address:** {my_organization[5]}, {my_organization[6]}")
        status = my_organization[8]
        if status == "VERIFIED":
            st.success("Verified. You can request food pickups.")
        elif status == "REJECTED":
            st.error(
                "Not approved. Reason: "
                f"{my_organization[10] or 'not given'}. "
                "Please contact an admin."
            )
        else:
            st.info("Waiting for an admin to verify your organization.")
    else:
        st.write("Register the organization that will receive food.")
        with st.form("my_organization_form"):
            organization_name = st.text_input("Organization name")
            contact_person = st.text_input(
                "Contact person", value=user["full_name"] or ""
            )
            phone = st.text_input("Phone", value=user["phone"] or "")
            email = st.text_input("Email", value=user["email"])
            address = st.text_area("Address")
            city = st.text_input("City", value=user["city"] or "")
            organization_type = st.selectbox(
                "Organization type",
                ["NGO", "Charity", "Food Bank",
                 "Community Organization", "Other"],
            )
            if st.form_submit_button("Register", type="primary"):
                if not organization_name.strip():
                    st.error("Organization name is required.")
                else:
                    result = create_organization_from_api({
                        "organization_name": organization_name,
                        "contact_person": contact_person,
                        "phone": phone,
                        "email": email,
                        "address": address,
                        "city": city,
                        "organization_type": organization_type,
                    })
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        link_organization(
                            user["email"], result["organization_id"]
                        )
                        flash_success(
                            "Registered! An admin will verify your "
                            "organization soon."
                        )


def organizations_page(ctx):

    st.header("🏢 Organization / NGO Management")

    st.subheader("Register Organization")

    with st.form("organization_form"):

        organization_name = st.text_input(
            "Organization Name"
        )

        contact_person = st.text_input(
            "Contact Person"
        )

        phone = st.text_input(
            "Phone"
        )

        email = st.text_input(
            "Email"
        )

        address = st.text_area(
            "Address"
        )

        city = st.text_input(
            "City"
        )

        organization_type = st.selectbox(
            "Organization Type",
            [
                "NGO",
                "Charity",
                "Food Bank",
                "Community Organization",
                "Other"
            ]
        )

        submitted = st.form_submit_button(
            "Register Organization"
        )

        if submitted:

            organization_data = {
                "organization_name": organization_name,
                "contact_person": contact_person,
                "phone": phone,
                "email": email,
                "address": address,
                "city": city,
                "organization_type": organization_type
            }

            result = create_organization_from_api(
                organization_data
            )

            if "error" in result:

                st.error(
                    f"Error registering organization: "
                    f"{result['error']}"
                )

            else:

                flash_success(
                    f"Organization registered successfully! "
                    f"Organization ID: "
                    f"{result['organization_id']}"
                )

    st.divider()

    st.subheader("Verified Organizations")

    organization_response = (
        get_verified_organizations_from_api()
    )

    if "error" in organization_response:

        st.error(
            organization_response["error"]
        )

    else:

        organizations = organization_response["organizations"]

        if organizations:

            for organization in organizations:

                st.write(
                    f"**{organization[1]}** — "
                    f"{organization[2]} — "
                    f"{organization[6]} — "
                    f"{organization[7]}"
                )

        else:

            st.info(
                "No verified organizations available."
            )
