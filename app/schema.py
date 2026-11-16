"""Database tables.

ensure_schema() is safe to run any number of times: it creates missing
tables and adds missing columns, and never drops or changes data. The
app runs it once at start-up, so a fresh database (for example a new
Neon project) is ready without any manual SQL.
"""

from app.database import get_connection

STATEMENTS = [
    # 1. Restaurants (food donors)
    """
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
    """,
    # 2. Food donations
    """
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
    """,
    # 3. Organizations (receivers)
    """
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
    """,
    # reject_organization() writes this column; it was missing before.
    """
    ALTER TABLE organizations
        ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
    """,
    # 4. Volunteers
    """
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
    """,
    # 5. Pickup requests
    """
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
    """,
    # 6. App users (who may log in, and in which role)
    """
    CREATE TABLE IF NOT EXISTS app_users (
        email VARCHAR(255) PRIMARY KEY,
        full_name VARCHAR(150),
        phone VARCHAR(20),
        city VARCHAR(100),
        role VARCHAR(20) NOT NULL DEFAULT 'DONOR',
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
        restaurant_id INTEGER REFERENCES restaurants(restaurant_id),
        organization_id INTEGER REFERENCES organizations(organization_id),
        volunteer_id INTEGER REFERENCES volunteers(volunteer_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP,
        CONSTRAINT app_users_role_check
            CHECK (role IN ('ADMIN', 'DONOR', 'ORGANIZATION', 'VOLUNTEER')),
        CONSTRAINT app_users_status_check
            CHECK (status IN ('PENDING', 'ACTIVE', 'DISABLED'))
    );
    """,
]

# Extra safety nets. If old data breaks one of these rules the index is
# skipped (with a warning) instead of stopping the app from starting.
OPTIONAL_STATEMENTS = [
    # Only one active pickup per donation, enforced by the database too.
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_active_pickup_per_donation
        ON pickup_requests (donation_id)
        WHERE pickup_status IN ('REQUESTED', 'ACCEPTED', 'PICKED_UP');
    """,
]


def ensure_schema():
    connection = get_connection()
    cursor = connection.cursor()
    try:
        for statement in STATEMENTS:
            cursor.execute(statement)
        for statement in OPTIONAL_STATEMENTS:
            cursor.execute("SAVEPOINT optional_step;")
            try:
                cursor.execute(statement)
                cursor.execute("RELEASE SAVEPOINT optional_step;")
            except Exception as error:
                cursor.execute("ROLLBACK TO SAVEPOINT optional_step;")
                print(f"Warning: skipped optional schema step: {error}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
