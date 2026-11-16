import pytest

from app.organization_service import (
    add_organization,
    get_organization_summary,
    get_pending_organizations,
    get_verified_organizations,
    reject_organization,
    verify_organization,
)
from tests.conftest import query_one


def new_org(name="Hope Shelter"):
    return add_organization(
        name, "Mary", "8888888888", "hope@example.com",
        "45 Church Street", "Hyderabad", "NGO",
    )


def test_new_organization_waits_for_verification():
    organization_id = new_org()
    assert [row[0] for row in get_pending_organizations()] == [organization_id]
    assert get_verified_organizations() == []


def test_verify_organization():
    organization_id = new_org()
    verify_organization(organization_id)
    assert [row[0] for row in get_verified_organizations()] == [organization_id]
    with pytest.raises(ValueError, match="already verified"):
        verify_organization(organization_id)


def test_reject_organization_saves_reason():
    # This failed before: the rejection_reason column did not exist.
    organization_id = new_org()
    reject_organization(organization_id, "Could not confirm address")
    row = query_one(
        "SELECT verification_status, rejection_reason "
        "FROM organizations WHERE organization_id = %s;",
        (organization_id,),
    )
    assert row == ("REJECTED", "Could not confirm address")
    summary = get_organization_summary()
    assert summary["rejected_organizations"] == 1
