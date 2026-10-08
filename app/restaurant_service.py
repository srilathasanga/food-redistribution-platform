from app.database import get_connection


def add_restaurant(
    restaurant_name,
    contact_person,
    phone,
    email,
    address,
    city
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO restaurants
            (
                restaurant_name,
                contact_person,
                phone,
                email,
                address,
                city
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING restaurant_id;
        """, (
            restaurant_name,
            contact_person,
            phone,
            email,
            address,
            city
        ))

        restaurant_id = cursor.fetchone()[0]

        connection.commit()

        return restaurant_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_all_restaurants():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                restaurant_id,
                restaurant_name,
                contact_person,
                phone,
                email,
                address,
                city,
                status,
                created_at
            FROM restaurants
            ORDER BY restaurant_id;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()