"""Organizations: My organization and Organizations (admin)."""

import streamlit as st

from app import ui
from app.backend import (
    create_organization_from_api,
    get_pending_organizations_from_api,
    get_verified_organizations_from_api,
    link_organization,
    reject_organization_from_api,
    verify_organization_from_api,
)
from app.screens.kitchens import contact_problems

ORGANIZATION_TYPES = ["NGO", "Charity", "Food Bank", "Community Organization",
                      "Home or shelter", "Church", "Other"]


def _organization_form(form_key, submit_label, defaults=None):
    """The add-an-organization form. Returns the checked details, or None."""
    defaults = defaults or {}
    with st.form(form_key):
        col1, col2 = st.columns(2)
        name = col1.text_input("Organization name",
                               placeholder="e.g. Hope Shelter")
        organization_type = col2.selectbox("Type of organization",
                                           ORGANIZATION_TYPES)
        col1, col2 = st.columns(2)
        contact_person = col1.text_input(
            "Contact person", value=defaults.get("contact_person", ""),
            placeholder="e.g. Sister Mary",
        )
        phone = col2.text_input(
            "Phone", value=defaults.get("phone", ""),
            placeholder="10-digit mobile",
            help="Volunteers call this number when they deliver food.",
        )
        email = st.text_input("Email (optional)",
                              value=defaults.get("email", ""),
                              placeholder="e.g. office@example.org")
        address = st.text_area("Address", height=90,
                               placeholder="Where volunteers deliver food")
        city = st.text_input("City", value=defaults.get("city", ""),
                             placeholder="e.g. Hyderabad")
        if not st.form_submit_button(submit_label, type="primary",
                                     icon=":material/add:", width="stretch"):
            return None

        problems = [] if name.strip() else ["Please enter the organization "
                                            "name."]
        if not address.strip():
            problems.append("Please enter the address, so volunteers know "
                            "where to deliver.")
        problems += contact_problems(phone, email)
        for problem in problems:
            st.error(problem, icon=":material/error:")
        if problems:
            return None
        return {
            "organization_name": name.strip(),
            "organization_type": organization_type,
            "contact_person": contact_person.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "address": address.strip(),
            "city": city.strip(),
        }


def _organization_lines(organization):
    (_, _name, contact_person, phone, email, address, city,
     organization_type) = organization[:8]
    lines = []
    if organization_type:
        lines.append(f":material/category: {organization_type}")
    place = ", ".join(part for part in (address, city) if part)
    if place:
        lines.append(f":material/location_on: {place}")
    if contact_person:
        lines.append(f":material/person: {contact_person}")
    if phone:
        lines.append(f":material/call: [{phone}](tel:{phone})")
    if email:
        lines.append(f":material/mail: [{email}](mailto:{email})")
    return "  \n".join(lines)


# ---------------------------------------------------------------- organization

def my_organization_page(ctx):
    ui.page_header("My organization",
                   "The home, shelter or charity that receives food.",
                   icon=":material/apartment:")

    organization = ctx.my_organization
    if organization:
        status, reason = organization[8], organization[10]
        with ui.card():
            ui.person_header(organization[1], [organization[6],
                                               organization[7]])
            st.markdown(ui.badge_markdown(status))
            st.markdown(_organization_lines(organization))
        if status == "VERIFIED":
            st.success("You're verified. You can request food any time.",
                       icon=":material/verified:")
            if st.button("Find food to request", type="primary",
                         icon=":material/restaurant:", width="stretch"):
                st.switch_page(ctx.pages["available-food"])
        elif status == "REJECTED":
            st.error(f"Not approved. Reason: {reason or 'not given'}. "
                     "Please contact the ministry admin.",
                     icon=":material/block:")
        else:
            st.info("A coordinator will check your organization soon. "
                    "You'll be able to request food once it is verified.",
                    icon=":material/hourglass_top:")
        st.caption("To change these details, please contact the ministry "
                   "admin.")
        return

    st.markdown("Add the organization that receives food. A coordinator "
                "checks it before you can request food.")
    user = ctx.user
    details = _organization_form("my_organization_form",
                                 "Save my organization", {
                                     "contact_person": user["full_name"] or "",
                                     "phone": user["phone"] or "",
                                     "email": user["email"],
                                     "city": user["city"] or "",
                                 })
    if details:
        result = create_organization_from_api(details)
        if "error" in result:
            st.error(f"Could not save your organization: {result['error']}",
                     icon=":material/error:")
        else:
            link_organization(user["email"], result["organization_id"])
            ui.flash_success(
                f"{details['organization_name']} is saved. Next: a "
                "coordinator verifies it, then you can request food."
            )


# ---------------------------------------------------------------- admin

def organizations_page(ctx):
    ui.page_header(
        "Organizations",
        "Homes, shelters and charities that receive food. Verify new ones "
        "first.",
        icon=":material/groups:",
    )

    # Came from Home > "Add organization": show the form first, open.
    if ui.form_requested("organization"):
        _add_organization(expanded=True)
        add_form_shown = True
    else:
        add_form_shown = False

    # 1. The next action: organizations waiting to be checked.
    pending = ui.rows(get_pending_organizations_from_api(), "organizations")
    ui.section_title(f"Waiting for verification ({len(pending)})",
                     ":material/hourglass_top:", "coral")
    if not pending:
        st.success("Nobody is waiting. All organizations are checked.",
                   icon=":material/task_alt:")
    for column, organization in ui.grid(pending):
        organization_id, name = organization[0], organization[1]
        with column, ui.card():
            ui.person_header(name, [organization[6], organization[7]])
            st.markdown(ui.badge_markdown("PENDING"))
            st.markdown(_organization_lines(organization))
            col1, col2 = st.columns(2)
            if col1.button("Verify", key=f"verify_{organization_id}",
                           type="primary", icon=":material/verified:",
                           width="stretch"):
                result = verify_organization_from_api(organization_id)
                if "error" in result:
                    st.error(result["error"], icon=":material/error:")
                else:
                    ui.flash_success(
                        f"{name} is verified. Next: its people can now "
                        "request food."
                    )
            with col2.popover("Not approved", icon=":material/block:",
                              width="stretch"):
                reason = st.text_input(
                    "Why not? (they will see this)",
                    key=f"reason_{organization_id}",
                    placeholder="e.g. We could not confirm the address",
                )
                if st.button("Confirm: not approved",
                             key=f"reject_{organization_id}",
                             width="stretch"):
                    if not reason.strip():
                        st.error("Please give a reason.",
                                 icon=":material/error:")
                    else:
                        result = reject_organization_from_api(
                            organization_id, reason.strip())
                        if "error" in result:
                            st.error(result["error"], icon=":material/error:")
                        else:
                            ui.flash_success(f"{name} was marked as not "
                                             "approved.")

    # 2. Everyone already verified.
    verified = ui.rows(get_verified_organizations_from_api(),
                       "organizations")
    ui.section_title(ui.plural(len(verified), "verified organization"),
                     ":material/verified:", "green")
    if not verified:
        ui.empty_state(
            "No verified organizations yet",
            icon=":material/groups:", image="empty-people",
            hint="Organizations sign up themselves, or you can add one "
                 "below. Verify them above.",
        )
    for column, organization in ui.grid(verified):
        with column, ui.card():
            ui.person_header(organization[1], [organization[6],
                                               organization[7]])
            st.markdown(ui.badge_markdown("VERIFIED"))
            st.markdown(_organization_lines(organization))

    # 3. Add one on someone's behalf (rarely needed).
    if not add_form_shown:
        _add_organization(expanded=False)


def _add_organization(expanded):
    with st.expander("Add an organization", icon=":material/add_business:",
                     expanded=expanded):
        details = _organization_form("organization_form",
                                     "Add organization")
        if details:
            result = create_organization_from_api(details)
            if "error" in result:
                st.error(f"Could not add the organization: "
                         f"{result['error']}", icon=":material/error:")
            else:
                ui.flash_success(
                    f"{details['organization_name']} was added. Next: "
                    "verify it under \"Waiting for verification\"."
                )
