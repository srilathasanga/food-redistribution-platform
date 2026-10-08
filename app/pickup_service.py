from app.database import get_connection
from datetime import datetime


def request_pickup(
    donation_id,
    organization_id,
    pickup_time,
    pickup_address,
    notes
):
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # 0. Validate pickup time

        if pickup_time <= datetime.now():
            raise ValueError(
                "Pickup time must be in the future."
            )

        # 1. Check whether the organization is verified and active
        cursor.execute("""
            SELECT verification_status, status
            FROM organizations
            WHERE organization_id = %s;
        """, (organization_id,))

        organization = cursor.fetchone()

        if organization is None:
            raise ValueError("Organization not found.")

        verification_status, organization_status = organization

        if verification_status != "VERIFIED":
            raise ValueError(
                "Only verified organizations can request food."
            )

        if organization_status != "ACTIVE":
            raise ValueError(
                "Inactive organizations cannot request food."
            )

        # 2. Check whether the donation exists,
        #    is available, and has not expired
        cursor.execute("""
            SELECT donation_status, expiry_time
            FROM food_donations
            WHERE donation_id = %s;
        """, (donation_id,))

        donation = cursor.fetchone()

        if donation is None:
            raise ValueError("Food donation not found.")

        donation_status, expiry_time = donation

        if donation_status != "AVAILABLE":
            raise ValueError(
                "This food donation is no longer available."
            )

        if expiry_time is not None:
            cursor.execute("""
                SELECT CURRENT_TIMESTAMP < %s;
            """, (expiry_time,))

            is_valid = cursor.fetchone()[0]

            if not is_valid:
                raise ValueError(
                    "This food donation has expired."
                )

        # 3. Check for an existing active pickup request
        cursor.execute("""
            SELECT pickup_id
            FROM pickup_requests
            WHERE donation_id = %s
              AND pickup_status IN
                  ('REQUESTED', 'ACCEPTED', 'PICKED_UP');
        """, (donation_id,))

        existing_pickup = cursor.fetchone()

        if existing_pickup is not None:
            raise ValueError(
                f"This donation already has an active "
                f"pickup request (Pickup ID: {existing_pickup[0]})."
            )

        # 4. Create the pickup request
        cursor.execute("""
            INSERT INTO pickup_requests
            (
                donation_id,
                organization_id,
                pickup_time,
                pickup_address,
                notes
            )
            VALUES
            (%s, %s, %s, %s, %s)
            RETURNING pickup_id;
        """, (
            donation_id,
            organization_id,
            pickup_time,
            pickup_address,
            notes
        ))

        pickup_id = cursor.fetchone()[0]

        connection.commit()

        return pickup_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



def get_all_pickup_requests():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.pickup_id,
                f.food_name,
                f.quantity,
                f.unit,
                r.restaurant_name,
                o.organization_name,
                p.requested_at,
                p.pickup_time,
                p.pickup_status,
                p.pickup_address,
                p.notes,
                p.volunteer_id,
                v.volunteer_name

            FROM pickup_requests p

            JOIN food_donations f
                ON p.donation_id = f.donation_id

            JOIN restaurants r
                ON f.restaurant_id = r.restaurant_id

            JOIN organizations o
                ON p.organization_id = o.organization_id

            LEFT JOIN volunteers v
                ON p.volunteer_id = v.volunteer_id

            ORDER BY p.pickup_id;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


## To update Pickup service
def update_pickup_status(pickup_id, new_status):
    allowed_statuses = [
        "REQUESTED",
        "ACCEPTED",
        "PICKED_UP",
        "DELIVERED"
    ]

    valid_transitions = {
        "REQUESTED": ["ACCEPTED"],
        "ACCEPTED": ["PICKED_UP"],
        "PICKED_UP": ["DELIVERED"],
        "DELIVERED": []
    }

    donation_status_map = {
        "ACCEPTED": "RESERVED",
        "PICKED_UP": "PICKED_UP",
        "DELIVERED": "DELIVERED"
    }

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid status: {new_status}"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Get current pickup status and related donation
        cursor.execute("""
            SELECT
                pickup_status,
                donation_id,
                volunteer_id
            FROM pickup_requests
            WHERE pickup_id = %s;
        """, (pickup_id,))

        result = cursor.fetchone()

        if result is None:
            raise ValueError("Pickup request not found.")

        current_status = result[0]
        donation_id = result[1]
        volunteer_id = result[2]

        # Validate status transition
        if new_status not in valid_transitions[current_status]:
            raise ValueError(
                f"Invalid transition: "
                f"{current_status} -> {new_status}"
            )

        # Update pickup status
        cursor.execute("""
            UPDATE pickup_requests
            SET pickup_status = %s
            WHERE pickup_id = %s;
        """, (
            new_status,
            pickup_id
        ))

        # Update related donation status
        if new_status in donation_status_map:
            donation_status = donation_status_map[new_status]

            cursor.execute("""
                UPDATE food_donations
                SET donation_status = %s
                WHERE donation_id = %s;
            """, (
                donation_status,
                donation_id
            ))
        # Make volunteer available again after delivery
        if new_status == "DELIVERED" and volunteer_id is not None:
            cursor.execute("""
             UPDATE volunteers 
             SET availability_status = 'AVAILABLE'
              WHERE volunteer_id = %s; """, (volunteer_id,))
        connection.commit()

        return pickup_id, new_status

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
##Assign a volunteer to pickup
def assign_volunteer(pickup_id, volunteer_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Check volunteer availability
        cursor.execute(
            """
            SELECT
                availability_status,
                volunteer_status
            FROM volunteers
            WHERE volunteer_id = %s
            """,
            (volunteer_id,)
        )

        volunteer = cursor.fetchone()

        if not volunteer:
            raise Exception("Volunteer not found.")

        availability_status = volunteer[0]
        volunteer_status = volunteer[1]

        if volunteer_status != "ACTIVE":
            raise Exception(
                "Volunteer is not active."
            )

        if availability_status != "AVAILABLE":
            raise Exception(
                "Volunteer is not available."
            )

        # Check pickup status
        cursor.execute(
            """
            SELECT pickup_status
            FROM pickup_requests
            WHERE pickup_id = %s
            """,
            (pickup_id,)
        )

        pickup = cursor.fetchone()

        if not pickup:
            raise Exception(
                "Pickup request not found."
            )

        if pickup[0] != "ACCEPTED":
            raise Exception(
                "Volunteer can only be assigned "
                "to an ACCEPTED pickup."
            )

        # Assign volunteer to pickup
        cursor.execute(
            """
            UPDATE pickup_requests
            SET volunteer_id = %s
            WHERE pickup_id = %s
            """,
            (
                volunteer_id,
                pickup_id
            )
        )

        # Mark volunteer as busy
        cursor.execute(
            """
            UPDATE volunteers
            SET availability_status = 'BUSY'
            WHERE volunteer_id = %s
            """,
            (volunteer_id,)
        )

        conn.commit()

        return {
            "pickup_id": pickup_id,
            "volunteer_id": volunteer_id
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
##Pickup summary function ##

def get_pickup_summary():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_pickups,

                COUNT(*) FILTER (
                    WHERE pickup_status = 'REQUESTED'
                ) AS requested_pickups,

                COUNT(*) FILTER (
                    WHERE pickup_status = 'ACCEPTED'
                ) AS accepted_pickups,

                COUNT(*) FILTER (
                    WHERE pickup_status = 'PICKED_UP'
                ) AS picked_up_pickups,

                COUNT(*) FILTER (
                    WHERE pickup_status = 'DELIVERED'
                ) AS delivered_pickups

            FROM pickup_requests;
        """)

        result = cursor.fetchone()

        return {
            "total_pickups": result[0],
            "requested_pickups": result[1],
            "accepted_pickups": result[2],
            "picked_up_pickups": result[3],
            "delivered_pickups": result[4]
        }

    finally:

        cursor.close()
        conn.close()

