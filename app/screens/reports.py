"""Reports & tools (admin)."""

import streamlit as st

from app import ui
from app.backend import (
    create_volunteer_from_api,
    get_donation_summary_from_api,
    get_food_risk_analysis_from_api,
    get_organization_summary_from_api,
    get_pending_organizations_from_api,
    get_pickup_summary_from_api,
    get_volunteer_summary_from_api,
    get_volunteers_from_api,
    reject_organization_from_api,
    verify_organization_from_api,
)

flash_success = ui.flash_success


def reports_page(ctx):

    st.header("👨‍💼 Admin Dashboard")

    # -----------------------------------------------------
    # VOLUNTEER SUMMARY
    # -----------------------------------------------------

    summary = get_volunteer_summary_from_api()

    if "error" in summary:

        st.error(summary["error"])

    else:

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "👥 Total Volunteers",
                summary["total_volunteers"]
            )

        with col2:

            st.metric(
                "✅ Active Volunteers",
                summary["active_volunteers"]
            )

        with col3:

            st.metric(
                "🟢 Available Volunteers",
                summary["available_volunteers"]
            )

        with col4:

            st.metric(
                "🚚 Busy Volunteers",
                summary["busy_volunteers"]
            )

    # -----------------------------------------------------
    # ORGANIZATION SUMMARY
    # -----------------------------------------------------

    organization_summary = (
        get_organization_summary_from_api()
    )

    if "error" in organization_summary:

        st.error(
            organization_summary["error"]
        )

    else:

        st.subheader("🏢 Organization Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "🏢 Total Organizations",
                organization_summary["total_organizations"]
            )

        with col2:

            st.metric(
                "✅ Verified",
                organization_summary["verified_organizations"]
            )

        with col3:

            st.metric(
                "⏳ Pending",
                organization_summary["pending_organizations"]
            )

        with col4:

            st.metric(
                "❌ Rejected",
                organization_summary["rejected_organizations"]
            )

    # -----------------------------------------------------
    # DONATION SUMMARY
    # -----------------------------------------------------

    donation_summary = get_donation_summary_from_api()

    if "error" in donation_summary:

        st.error(
            donation_summary["error"]
        )

    else:

        st.subheader("🍱 Donation Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "🍱 Total Donations",
                donation_summary["total_donations"]
            )

        with col2:

            st.metric(
                "🟢 Available",
                donation_summary["available_donations"]
            )

        with col3:

            st.metric(
                "🔒 Reserved",
                donation_summary["reserved_donations"]
            )

        with col4:

            st.metric(
                "🚚 Picked Up",
                donation_summary["picked_up_donations"]
            )

        with col5:

            st.metric(
                "✅ Delivered",
                donation_summary["delivered_donations"]
            )
        st.subheader("📊 Donation Status")

        donation_chart_data = {
            "Status": [
                "Available",
                "Reserved",
                "Picked Up",
                "Delivered"
            ],
            "Count": [
                donation_summary["available_donations"],
                donation_summary["reserved_donations"],
                donation_summary["picked_up_donations"],
                donation_summary["delivered_donations"]
            ]
        }

        st.bar_chart(
            donation_chart_data,
            x="Status",
            y="Count"
        )

    # -----------------------------------------------------
    # PICKUP SUMMARY
    # -----------------------------------------------------

    pickup_summary = get_pickup_summary_from_api()

    if "error" in pickup_summary:

        st.error(
            pickup_summary["error"]
        )

    else:

        st.subheader("🚚 Pickup Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "🚚 Total Pickups",
                pickup_summary["total_pickups"]
            )

        with col2:

            st.metric(
                "📋 Requested",
                pickup_summary["requested_pickups"]
            )

        with col3:

            st.metric(
                "🤝 Accepted",
                pickup_summary["accepted_pickups"]
            )

        with col4:

            st.metric(
                "📦 Picked Up",
                pickup_summary["picked_up_pickups"]
            )

        with col5:

            st.metric(
                "✅ Delivered",
                pickup_summary["delivered_pickups"]
            )
        st.subheader("📊 Pickup Status")

        pickup_chart_data = {
            "Status": [
                "Requested",
                "Accepted",
                "Picked Up",
                "Delivered"
            ],
            "Count": [
                pickup_summary["requested_pickups"],
                pickup_summary["accepted_pickups"],
                pickup_summary["picked_up_pickups"],
                pickup_summary["delivered_pickups"]
            ]
        }

        st.bar_chart(
            pickup_chart_data,
            x="Status",
            y="Count"
        )

    # =====================================================
    # AI FOOD RISK ANALYSIS
    # =====================================================

    st.subheader("🤖 AI Food Risk Analysis")

    risk_response = get_food_risk_analysis_from_api()

    if "error" in risk_response:

        st.error(
            risk_response["error"]
        )

    else:

        risk_results = risk_response.get(
            "risk_analysis",
            []
        )

        if not risk_results:

            st.success(
                "No active donations require risk analysis. ✅"
            )

        else:

            # -------------------------------------------------
            # AI RISK SUMMARY
            # -------------------------------------------------

            high_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "HIGH"
            )

            medium_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "MEDIUM"
            )

            low_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "LOW"
            )

            expired_count = sum(
                1
                for risk in risk_results
                if risk["risk_level"] == "EXPIRED"
            )

            st.markdown(
                "### 📊 AI Risk Summary"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "🔴 High Risk",
                    high_count
                )

            with col2:

                st.metric(
                    "🟠 Medium Risk",
                    medium_count
                )

            with col3:

                st.metric(
                    "🟢 Low Risk",
                    low_count
                )

            with col4:

                st.metric(
                    "⚫ Expired",
                    expired_count
                )
            st.subheader("📊 Food Risk Distribution")

            risk_chart_data = {
                "Risk Level": [
                    "HIGH",
                    "MEDIUM",
                    "LOW",
                    "EXPIRED"
                ],
                "Count": [
                    high_count,
                    medium_count,
                    low_count, 
                    expired_count
                ]
            }

            st.bar_chart(
                risk_chart_data,
                x="Risk Level",
                y="Count"
            )

            # -------------------------------------------------
            # INDIVIDUAL RISK ANALYSIS
            # -------------------------------------------------

            st.markdown(
                "### 🔍 Donation Risk Details"
            )

            risk_priority = {
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
                "EXPIRED": 4
            }

            risk_results = sorted(
                risk_results,
                key=lambda risk: (
                    risk_priority.get(
                        risk["risk_level"],
                        99
                    ),
                    risk["hours_remaining"]
                )
            )

            for risk in risk_results:

                st.markdown("---")

                st.write(
                    f"### 🍱 {risk['food_name']}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write(
                        f"**Donation ID:** "
                        f"{risk['donation_id']}"
                    )

                with col2:

                    st.write(
                        f"**Quantity:** "
                        f"{risk['quantity']} "
                        f"{risk['unit']}"
                    )

                with col3:

                    st.write(
                        f"**Risk:** "
                        f"{risk['risk_level']}"
                    )

                with col4:

                    st.write(
                        f"**Score:** "
                        f"{risk['risk_score']}"
                    )

                st.write(
                    f"**Priority:** "
                    f"{risk['priority']}"
                )

                st.info(
                    f"**🤖 Recommended Action:** "
                    f"{risk['recommended_action']}"
                )

                st.write(
                    f"**Hours Remaining:** "
                    f"{risk['hours_remaining']}"
                )

                st.write("**Reasons:**")

                for reason in risk["reasons"]:

                    st.write(
                        f"- {reason}"
                    )

    # -----------------------------------------------------
    # PENDING ORGANIZATIONS
    # -----------------------------------------------------

    st.divider()

    st.subheader("Pending Organizations")

    try:

        organization_response = (
            get_pending_organizations_from_api()
        )

        if "error" in organization_response:

            st.error(
                organization_response["error"]
            )

            organizations = []

        else:

            organizations = (
                organization_response["organizations"]
            )

        if organizations:

            for organization in organizations:

                organization_id = organization[0]
                organization_name = organization[1]
                contact_person = organization[2]
                phone = organization[3]
                email = organization[4]
                address = organization[5]
                city = organization[6]
                organization_type = organization[7]
                verification_status = organization[8]
                status = organization[9]

                st.markdown("---")

                st.subheader(
                    f"🏢 {organization_name}"
                )

                st.write(
                    f"**Organization ID:** "
                    f"{organization_id}"
                )

                st.write(
                    f"**Contact Person:** "
                    f"{contact_person}"
                )

                st.write(
                    f"**Phone:** {phone}"
                )

                st.write(
                    f"**Email:** {email}"
                )

                st.write(
                    f"**Address:** {address}"
                )

                st.write(
                    f"**City:** {city}"
                )

                st.write(
                    f"**Organization Type:** "
                    f"{organization_type}"
                )

                st.write(
                    f"**Verification Status:** "
                    f"{verification_status}"
                )

                st.write(
                    f"**Status:** {status}"
                )

                st.write(
                    "### Admin Decision"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "✅ Verify Organization",
                        key=f"verify_{organization_id}"
                    ):

                        result = (
                            verify_organization_from_api(
                                organization_id
                            )
                        )

                        if "error" in result:

                            st.error(
                                f"Error verifying organization: "
                                f"{result['error']}"
                            )

                        else:

                            flash_success(
                                f"Organization "
                                f"#{result['organization_id']} "
                                f"verified successfully!"
                            )

                with col2:

                    rejection_reason = st.text_input(
                        "Rejection Reason",
                        key=f"reason_{organization_id}",
                        placeholder="Enter reason for rejection"
                    )

                    if st.button(
                        "❌ Reject Organization",
                        key=f"reject_{organization_id}"
                    ):

                        if not rejection_reason.strip():

                            st.warning(
                                "Please enter a rejection reason."
                            )

                        else:

                            result = (
                                reject_organization_from_api(
                                    organization_id,
                                    rejection_reason
                                )
                            )

                            if "error" in result:

                                st.error(
                                    f"Error rejecting organization: "
                                    f"{result['error']}"
                                )

                            else:

                                flash_success(
                                    f"Organization "
                                    f"#{result['organization_id']} "
                                    f"has been rejected successfully!"
                                )

        else:

            st.success(
                "No organizations are waiting "
                "for verification. ✅"
            )

    except Exception as e:

        st.error(
            f"Error loading pending organizations: {e}"
        )

    # -----------------------------------------------------
    # VOLUNTEER MANAGEMENT
    # -----------------------------------------------------

    st.divider()

    st.subheader("🚗 Volunteer Management")

    st.write("### Add Volunteer")

    with st.form("volunteer_form"):

        volunteer_name = st.text_input(
            "Volunteer Name"
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

        submitted = st.form_submit_button(
            "Add Volunteer"
        )

        if submitted:

            if not volunteer_name.strip():

                st.error(
                    "Volunteer name is required."
                )

            elif not phone.strip():

                st.error(
                    "Phone number is required."
                )

            elif not city.strip():

                st.error(
                    "City is required."
                )

            else:

                volunteer_data = {
                    "volunteer_name": volunteer_name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "city": city
                }

                result = create_volunteer_from_api(
                    volunteer_data
                )

                if "error" in result:

                    st.error(
                        f"Error creating volunteer: "
                        f"{result['error']}"
                    )

                else:

                    flash_success(
                        f"Volunteer created successfully! "
                        f"Volunteer ID: "
                        f"{result['volunteer_id']}"
                    )

    st.divider()

    st.write("### Registered Volunteers")

    volunteer_response = get_volunteers_from_api()

    if "error" in volunteer_response:

        st.error(
            volunteer_response["error"]
        )

    else:

        volunteers = volunteer_response["volunteers"]

        if volunteers:

            for volunteer in volunteers:

                st.write(
                    f"**{volunteer[1]}** — "
                    f"{volunteer[2]} — "
                    f"{volunteer[5]} — "
                    f"Availability: {volunteer[6]} — "
                    f"Status: {volunteer[7]}"
                )

        else:

            st.info(
                "No volunteers registered yet."
            )
