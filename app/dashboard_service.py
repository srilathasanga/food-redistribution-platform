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
                (SELECT COUNT(*) FROM pickup_requests
                  WHERE pickup_status = 'ACCEPTED'
                    AND volunteer_id IS NULL),
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
            "pickups_needing_volunteer": row[4],
            "people_to_approve": row[5],
            "organizations_to_verify": row[6],
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


def get_impact_summary(month_start):
    """The ministry's impact, for the Home "impact strip" (one query).

    kg_this_month counts donations measured in kg since month_start;
    donations_this_month counts every donation since then, whatever the
    unit. The numbers are totals for everyone, not about one person.
    kitchens, organizations (verified) and volunteers also drive the
    admin's "Getting started" checklist before the first delivery.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT
                (SELECT COALESCE(SUM(quantity), 0) FROM food_donations
                  WHERE LOWER(unit) = 'kg' AND created_at >= %s),
                (SELECT COUNT(*) FROM food_donations
                  WHERE created_at >= %s),
                (SELECT COUNT(*) FROM pickup_requests
                  WHERE pickup_status = 'DELIVERED'),
                (SELECT COUNT(*) FROM restaurants
                  WHERE status = 'ACTIVE'),
                (SELECT COUNT(*) FROM volunteers
                  WHERE volunteer_status = 'ACTIVE'),
                (SELECT COUNT(*) FROM organizations
                  WHERE verification_status = 'VERIFIED');
        """, (month_start, month_start))
        row = cursor.fetchone()
        return {
            "kg_this_month": float(row[0]),
            "donations_this_month": row[1],
            "deliveries": row[2],
            "kitchens": row[3],
            "volunteers": row[4],
            "organizations": row[5],
        }
    finally:
        cursor.close()
        connection.close()
