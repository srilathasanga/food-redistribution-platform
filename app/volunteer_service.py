from app.database import get_connection


def add_volunteer(
    volunteer_name,
    phone,
    email,
    address,
    city
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO volunteers (
                volunteer_name,
                phone,
                email,
                address,
                city
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING volunteer_id
        """

        cursor.execute(
            query,
            (
                volunteer_name,
                phone,
                email,
                address,
                city
            )
        )

        volunteer_id = cursor.fetchone()[0]

        conn.commit()

        return volunteer_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def get_all_volunteers():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                volunteer_id,
                volunteer_name,
                phone,
                email,
                address,
                city,
                availability_status,
                volunteer_status,
                created_at
            FROM volunteers
            ORDER BY volunteer_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

##volunteer summary function###

def get_volunteer_summary():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                COUNT(*) AS total_volunteers,

                COUNT(*) FILTER (
                    WHERE volunteer_status = 'ACTIVE'
                ) AS active_volunteers,

                COUNT(*) FILTER (
                    WHERE availability_status = 'AVAILABLE'
                    AND volunteer_status = 'ACTIVE'
                ) AS available_volunteers,

                COUNT(*) FILTER (
                    WHERE availability_status = 'BUSY'
                    AND volunteer_status = 'ACTIVE'
                ) AS busy_volunteers

            FROM volunteers;
        """)

        result = cursor.fetchone()

        return {
            "total_volunteers": result[0],
            "active_volunteers": result[1],
            "available_volunteers": result[2],
            "busy_volunteers": result[3]
        }

    finally:

        cursor.close()
        conn.close()

