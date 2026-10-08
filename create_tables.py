from app.database import get_connection

##1. Restrauant Table creation
def create_restaurants_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            restaurant_id SERIAL PRIMARY KEY,
            restaurant_name VARCHAR(150) NOT NULL,
            contact_person VARCHAR(100),
            phone VARCHAR(20),
            email VARCHAR(150),
            address TEXT,
            city VARCHAR(100),
            status VARCHAR(20) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Restaurants table created successfully!")



###2. Food donations table Creation

def create_food_donations_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_donations (
            donation_id SERIAL PRIMARY KEY,
            restaurant_id INTEGER NOT NULL,
            food_name VARCHAR(200) NOT NULL,
            food_category VARCHAR(100),
            quantity DECIMAL(10, 2) NOT NULL,
            unit VARCHAR(30),
            prepared_time TIMESTAMP,
            expiry_time TIMESTAMP,
            food_type VARCHAR(30),
            packaging_status VARCHAR(50),
            pickup_address TEXT,
            donation_status VARCHAR(30) DEFAULT 'AVAILABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_restaurant
                FOREIGN KEY (restaurant_id)
                REFERENCES restaurants(restaurant_id)
        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Food donations table created successfully!")

## 3. Organization Table Creation

def create_organizations_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            organization_id SERIAL PRIMARY KEY,
            organization_name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(100),
            phone VARCHAR(20),
            email VARCHAR(150),
            address TEXT,
            city VARCHAR(100),
            organization_type VARCHAR(100),
            verification_status VARCHAR(30) DEFAULT 'PENDING',
            status VARCHAR(20) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Organizations table created successfully!")


## 4. Volunteer Table Creation

def create_volunteers_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS volunteers (
            volunteer_id SERIAL PRIMARY KEY,
            volunteer_name VARCHAR(150) NOT NULL,
            phone VARCHAR(20),
            email VARCHAR(150),
            address TEXT,
            city VARCHAR(100),
            availability_status VARCHAR(20) DEFAULT 'AVAILABLE',
            volunteer_status VARCHAR(20) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Volunteers table created successfully!")

## 4. Pickup request table creation
def create_pickup_requests_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pickup_requests (
    pickup_id SERIAL PRIMARY KEY,
    donation_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    volunteer_id INTEGER,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pickup_time TIMESTAMP,
    pickup_status VARCHAR(30) DEFAULT 'REQUESTED',
    pickup_address TEXT,
    notes TEXT,

    CONSTRAINT fk_donation
        FOREIGN KEY (donation_id)
        REFERENCES food_donations(donation_id),

    CONSTRAINT fk_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id),

    CONSTRAINT fk_volunteer
        FOREIGN KEY (volunteer_id)
        REFERENCES volunteers(volunteer_id)
    );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Pickup requests table created successfully!")

if __name__ == "__main__":
    create_restaurants_table()
    create_food_donations_table()
    create_organizations_table()
    create_volunteers_table()
    create_pickup_requests_table()