"""Read-only numbers for the Home pages.

Each function is ONE query, because every round trip to the database
costs time (about 0.26 s from India to Neon in the US).
"""

from app.database import get_connection

# Same rule as food_risk_service: "HIGH" risk = under 2 hours left.
URGENT_HOURS = 2


def get_admin_home_counts():
    """Today's numbers for the admin Home page, in a single query."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"""
            SELECT
                (SELECT COUNT(*) FROM food_donations
                  WHERE donation_status = 'AVAILABLE'
                    AND expiry_time > CURRENT_TIMESTAMP),
                (SELECT COUNT(*) FROM food_donations
                  WHERE donation_status IN ('AVAILABLE', 'RESERVED')
                    AND expiry_time > CURRENT_TIMESTAMP
                    AND expiry_time < CURRENT_TIMESTAMP
                                      + INTERVAL '{URGENT_HOURS} hours'),
                (SELECT COUNT(*) FROM food_donations
                  WHERE donation_status = 'AVAILABLE'
                    AND expiry_time <= CURRENT_TIMESTAMP),
                (SELECT COUNT(*) FROM pickup_requests
                  WHERE pickup_status = 'REQUESTED'),
                (SELECT COUNT(*) FROM app_users
                  WHERE status = 'PENDING'),
                (SELECT COUNT(*) FROM organizations
                  WHERE verification_status = 'PENDING');
        """)
        row = cursor.fetchone()
        return {
            "food_available": row[0],
            "urgent": row[1],
            "expired_uncollected": row[2],
            "pickups_to_accept": row[3],
            "people_to_approve": row[4],
            "organizations_to_verify": row[5],
        }
    finally:
        cursor.close()
        connection.close()


def get_urgent_food():
    """Food that expires in under 2 hours and is not collected yet,
    soonest first."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"""
            SELECT donation_id, food_name, quantity, unit, expiry_time,
                   donation_status
            FROM food_donations
            WHERE donation_status IN ('AVAILABLE', 'RESERVED')
              AND expiry_time > CURRENT_TIMESTAMP
              AND expiry_time < CURRENT_TIMESTAMP
                                + INTERVAL '{URGENT_HOURS} hours'
            ORDER BY expiry_time;
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
