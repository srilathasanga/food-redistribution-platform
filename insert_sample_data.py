from app.database import get_connection


def insert_sample_data():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # 1. Insert a sample restaurant
        cursor.execute("""
            INSERT INTO restaurants
            (restaurant_name, contact_person, phone, email, address, city)
            VALUES
            (%s, %s, %s, %s, %s, %s)
            RETURNING restaurant_id;
        """, (
            "Green Leaf Restaurant",
            "Anil Kumar",
            "9999999999",
            "greenleaf@example.com",
            "123 Main Road",
            "Hyderabad"
        ))

        restaurant_id = cursor.fetchone()[0]

        # 2. Insert a sample food donation
        cursor.execute("""
            INSERT INTO food_donations
            (restaurant_id, food_name, food_category, quantity, unit,
             prepared_time, expiry_time, food_type,
             packaging_status, pickup_address)
            VALUES
            (%s, %s, %s, %s, %s,
             CURRENT_TIMESTAMP,
             CURRENT_TIMESTAMP + INTERVAL '6 hours',
             %s, %s, %s)
            RETURNING donation_id;
        """, (
            restaurant_id,
            "Vegetable Rice",
            "Cooked Meals",
            25,
            "kg",
            "VEGETARIAN",
            "PACKED",
            "123 Main Road, Hyderabad"
        ))

        donation_id = cursor.fetchone()[0]

        # 3. Insert a sample organization
        cursor.execute("""
            INSERT INTO organizations
            (organization_name, contact_person, phone, email,
             address, city, organization_type, verification_status)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING organization_id;
        """, (
            "Helping Hands Foundation",
            "Priya Sharma",
            "8888888888",
            "helpinghands@example.com",
            "45 Community Road",
            "Hyderabad",
            "NGO",
            "VERIFIED"
        ))

        organization_id = cursor.fetchone()[0]

        # 4. Create a pickup request
        cursor.execute("""
            INSERT INTO pickup_requests
            (donation_id, organization_id, pickup_time,
             pickup_status, pickup_address, notes)
            VALUES
            (%s, %s,
             CURRENT_TIMESTAMP + INTERVAL '2 hours',
             %s, %s, %s);
        """, (
            donation_id,
            organization_id,
            "REQUESTED",
            "123 Main Road, Hyderabad",
            "Please collect the food within the safe consumption window."
        ))

        connection.commit()

        print("Sample data inserted successfully!")
        print("Restaurant ID:", restaurant_id)
        print("Donation ID:", donation_id)
        print("Organization ID:", organization_id)

    except Exception as e:
        connection.rollback()
        print("Error inserting sample data:")
        print(e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    insert_sample_data()