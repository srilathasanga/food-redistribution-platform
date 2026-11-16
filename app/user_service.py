"""App users: who may log in, in which role, and what they are linked to.

Roles
  ADMIN         ministry coordinators: everything
  DONOR         a restaurant / caterer / family: posts food donations
  ORGANIZATION  an NGO or home: requests pickups once verified
  VOLUNTEER     collects and delivers food assigned to them

A new person who logs in asks for access (status PENDING); an admin
approves them. Emails listed in ADMIN_EMAILS become admins automatically.
"""

from app.database import get_connection
from app.volunteer_service import add_volunteer

ROLES = ["ADMIN", "DONOR", "ORGANIZATION", "VOLUNTEER"]
SELF_SERVICE_ROLES = ["DONOR", "ORGANIZATION", "VOLUNTEER"]
STATUSES = ["PENDING", "ACTIVE", "DISABLED"]

USER_COLUMNS = (
    "email", "full_name", "phone", "city", "role", "status",
    "restaurant_id", "organization_id", "volunteer_id",
    "created_at", "last_login_at",
)
_SELECT = f"SELECT {', '.join(USER_COLUMNS)} FROM app_users"


def normalize_email(email):
    return (email or "").strip().lower()


def _row_to_user(row):
    return dict(zip(USER_COLUMNS, row)) if row else None


def _fetch_one(query, params):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def _write(query, params, returning=False):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        result = cursor.fetchone() if returning else None
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_user(email):
    row = _fetch_one(f"{_SELECT} WHERE email = %s;", (normalize_email(email),))
    return _row_to_user(row)


def ensure_admin(email, full_name=None):
    """Create or promote a bootstrap admin (from ADMIN_EMAILS)."""
    _write(
        """
        INSERT INTO app_users (email, full_name, role, status)
        VALUES (%s, %s, 'ADMIN', 'ACTIVE')
        ON CONFLICT (email) DO UPDATE
            SET role = 'ADMIN',
                status = 'ACTIVE',
                full_name = COALESCE(app_users.full_name, EXCLUDED.full_name);
        """,
        (normalize_email(email), full_name),
    )
    return get_user(email)


def record_login(email):
    _write(
        "UPDATE app_users SET last_login_at = CURRENT_TIMESTAMP WHERE email = %s;",
        (normalize_email(email),),
    )


def request_access(email, full_name, phone, city, role):
    email = normalize_email(email)
    if not email:
        raise ValueError("Email is required.")
    if not (full_name or "").strip():
        raise ValueError("Name is required.")
    if role not in SELF_SERVICE_ROLES:
        raise ValueError("Please choose Donor, Organization or Volunteer.")

    existing = get_user(email)
    if existing and existing["status"] != "PENDING":
        raise ValueError("An account already exists for this email.")

    _write(
        """
        INSERT INTO app_users (email, full_name, phone, city, role, status)
        VALUES (%s, %s, %s, %s, %s, 'PENDING')
        ON CONFLICT (email) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                phone = EXCLUDED.phone,
                city = EXCLUDED.city,
                role = EXCLUDED.role;
        """,
        (email, full_name.strip(), phone, city, role),
    )
    return get_user(email)


def list_users(status=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if status:
            cursor.execute(
                f"{_SELECT} WHERE status = %s ORDER BY created_at;", (status,)
            )
        else:
            cursor.execute(f"{_SELECT} ORDER BY status, role, email;")
        return [_row_to_user(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()


def approve_user(email, role):
    """Activate a user in a role. A new volunteer gets a volunteer record."""
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    user = get_user(email)
    if user is None:
        raise ValueError("User not found.")

    volunteer_id = user["volunteer_id"]
    if role == "VOLUNTEER" and volunteer_id is None:
        if not (user["phone"] or "").strip():
            raise ValueError("A volunteer needs a phone number.")
        volunteer_id = add_volunteer(
            volunteer_name=user["full_name"] or user["email"],
            phone=user["phone"],
            email=user["email"],
            address="",
            city=user["city"] or "",
        )

    _write(
        """
        UPDATE app_users
        SET role = %s, status = 'ACTIVE', volunteer_id = %s
        WHERE email = %s;
        """,
        (role, volunteer_id, user["email"]),
    )
    return get_user(email)


def set_user_status(email, status):
    if status not in STATUSES:
        raise ValueError(f"Unknown status: {status}")
    result = _write(
        "UPDATE app_users SET status = %s WHERE email = %s RETURNING email;",
        (status, normalize_email(email)),
        returning=True,
    )
    if result is None:
        raise ValueError("User not found.")


def link_restaurant(email, restaurant_id):
    _write(
        "UPDATE app_users SET restaurant_id = %s WHERE email = %s;",
        (restaurant_id, normalize_email(email)),
    )


def link_organization(email, organization_id):
    _write(
        "UPDATE app_users SET organization_id = %s WHERE email = %s;",
        (organization_id, normalize_email(email)),
    )


def get_restaurant(restaurant_id):
    return _fetch_one(
        """
        SELECT restaurant_id, restaurant_name, contact_person, phone,
               email, address, city, status
        FROM restaurants WHERE restaurant_id = %s;
        """,
        (restaurant_id,),
    )


def get_organization(organization_id):
    return _fetch_one(
        """
        SELECT organization_id, organization_name, contact_person, phone,
               email, address, city, organization_type,
               verification_status, status, rejection_reason
        FROM organizations WHERE organization_id = %s;
        """,
        (organization_id,),
    )
