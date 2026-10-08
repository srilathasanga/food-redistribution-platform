from app.database import get_connection


def add_organization(
    organization_name,
    contact_person,
    phone,
    email,
    address,
    city,
    organization_type
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO organizations
            (
                organization_name,
                contact_person,
                phone,
                email,
                address,
                city,
                organization_type
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)
            RETURNING organization_id;
        """, (
            organization_name,
            contact_person,
            phone,
            email,
            address,
            city,
            organization_type
        ))

        organization_id = cursor.fetchone()[0]

        connection.commit()

        return organization_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_verified_organizations():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                organization_id,
                organization_name,
                contact_person,
                phone,
                email,
                address,
                city,
                organization_type,
                verification_status,
                status,
                created_at
            FROM organizations
            WHERE verification_status = 'VERIFIED'
              AND status = 'ACTIVE'
            ORDER BY organization_id;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


# =========================================================
# ADMIN FUNCTIONS
# =========================================================

def get_pending_organizations():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                organization_id,
                organization_name,
                contact_person,
                phone,
                email,
                address,
                city,
                organization_type,
                verification_status,
                status,
                created_at
            FROM organizations
            WHERE verification_status = 'PENDING'
            ORDER BY organization_id;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def verify_organization(organization_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE organizations
            SET verification_status = 'VERIFIED'
            WHERE organization_id = %s
              AND verification_status = 'PENDING'
            RETURNING organization_id;
        """, (organization_id,))

        result = cursor.fetchone()

        if result is None:
            raise ValueError(
                "Organization not found or already verified."
            )

        connection.commit()

        return result[0]

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
##Rejection for ngo verification
def reject_organization(organization_id, rejection_reason):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE organizations
            SET
                verification_status = 'REJECTED',
                rejection_reason = %s
            WHERE organization_id = %s
              AND verification_status = 'PENDING'
            RETURNING organization_id;
        """, (
            rejection_reason,
            organization_id
        ))

        result = cursor.fetchone()

        if result is None:
            raise ValueError(
                "Organization not found or already processed."
            )

        connection.commit()

        return result[0]

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
##org.summary in admin dashboard##

def get_organization_summary():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_organizations,

                COUNT(*) FILTER (
                    WHERE verification_status = 'VERIFIED'
                ) AS verified_organizations,

                COUNT(*) FILTER (
                    WHERE verification_status = 'PENDING'
                ) AS pending_organizations,

                COUNT(*) FILTER (
                    WHERE verification_status = 'REJECTED'
                ) AS rejected_organizations

            FROM organizations;
        """)

        result = cursor.fetchone()

        return {
            "total_organizations": result[0],
            "verified_organizations": result[1],
            "pending_organizations": result[2],
            "rejected_organizations": result[3]
        }

    finally:

        cursor.close()
        conn.close()

