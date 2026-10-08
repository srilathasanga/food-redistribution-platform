from app.database import get_connection


def add_food_donation(
    restaurant_id,
    food_name,
    food_category,
    quantity,
    unit,
    prepared_time,
    expiry_time,
    food_type,
    packaging_status,
    pickup_address
):
    # -----------------------------
    # INPUT VALIDATION
    # -----------------------------

    if not food_name or not food_name.strip():
        raise ValueError("Food name is required.")

    if quantity is None or quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    if not unit or not unit.strip():
        raise ValueError("Unit is required.")

    if prepared_time is None:
        raise ValueError("Prepared time is required.")

    if expiry_time is None:
        raise ValueError("Expiry time is required.")

    if expiry_time <= prepared_time:
        raise ValueError(
            "Expiry time must be after prepared time."
        )

    allowed_food_types = [
        "VEGETARIAN",
        "NON_VEGETARIAN"
    ]

    if food_type not in allowed_food_types:
        raise ValueError(
            "Invalid food type. Use VEGETARIAN or NON_VEGETARIAN."
        )

    allowed_packaging_statuses = [
        "PACKED",
        "UNPACKED"
    ]

    if packaging_status not in allowed_packaging_statuses:
        raise ValueError(
            "Invalid packaging status. Use PACKED or UNPACKED."
        )

    # -----------------------------
    # DATABASE OPERATION
    # -----------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether restaurant exists
        cursor.execute("""
            SELECT restaurant_id
            FROM restaurants
            WHERE restaurant_id = %s;
        """, (restaurant_id,))

        restaurant = cursor.fetchone()

        if restaurant is None:
            raise ValueError(
                "Restaurant not found."
            )

        # Insert donation
        cursor.execute("""
            INSERT INTO food_donations
            (
                restaurant_id,
                food_name,
                food_category,
                quantity,
                unit,
                prepared_time,
                expiry_time,
                food_type,
                packaging_status,
                pickup_address
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING donation_id;
        """, (
            restaurant_id,
            food_name,
            food_category,
            quantity,
            unit,
            prepared_time,
            expiry_time,
            food_type,
            packaging_status,
            pickup_address
        ))

        donation_id = cursor.fetchone()[0]

        connection.commit()

        return donation_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_available_donations():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                f.donation_id,
                r.restaurant_name,
                f.food_name,
                f.food_category,
                f.quantity,
                f.unit,
                f.prepared_time,
                f.expiry_time,
                f.food_type,
                f.packaging_status,
                f.pickup_address,
                f.donation_status
            FROM food_donations f
            JOIN restaurants r
                ON f.restaurant_id = r.restaurant_id
            WHERE f.donation_status = 'AVAILABLE'
              AND f.expiry_time > CURRENT_TIMESTAMP
            ORDER BY f.expiry_time;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

## Donation Summary function ##

def get_donation_summary():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_donations,

                COUNT(*) FILTER (
                    WHERE donation_status = 'AVAILABLE'
                ) AS available_donations,

                COUNT(*) FILTER (
                    WHERE donation_status = 'RESERVED'
                ) AS reserved_donations,

                COUNT(*) FILTER (
                    WHERE donation_status = 'PICKED_UP'
                ) AS picked_up_donations,

                COUNT(*) FILTER (
                    WHERE donation_status = 'DELIVERED'
                ) AS delivered_donations

            FROM food_donations;
        """)

        result = cursor.fetchone()

        return {
            "total_donations": result[0],
            "available_donations": result[1],
            "reserved_donations": result[2],
            "picked_up_donations": result[3],
            "delivered_donations": result[4]
        }

    finally:

        cursor.close()
        conn.close()

