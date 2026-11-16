# Food Redistribution Platform

A real-world food redistribution platform built with **Python, FastAPI, Streamlit, and PostgreSQL** to connect restaurants with verified organizations and volunteers for efficient food donation, pickup, and delivery.

## 📌 Project Overview

The Food Redistribution Platform helps reduce food wastage by providing a structured workflow for restaurants to donate surplus food and for verified organizations to request and receive those donations.

The platform manages the complete lifecycle of a food donation:

**Restaurant → Donation → Organization Verification → Pickup Request → Volunteer Assignment → Pickup → Delivery**

The application was developed as a personal project to understand how a real-world Python backend, database, business workflow, validation, and testing can work together.

## 🎯 Key Objectives

* Allow restaurants to register surplus food donations.
* Maintain organization/NGO information and verification status.
* Allow verified organizations to request available donations.
* Assign available volunteers to pickup requests.
* Track donation and pickup status throughout the lifecycle.
* Validate donation information before processing.
* Maintain data persistence using PostgreSQL.
* Provide automated tests for important business scenarios.
* Provide a simple UI using Streamlit.
* Expose backend functionality through FastAPI APIs.

## 🛠️ Technology Stack

| Technology    | Purpose                               |
| ------------- | ------------------------------------- |
| Python        | Application and business logic        |
| FastAPI       | Optional REST API (`app/main.py`)     |
| Streamlit     | User interface                        |
| PostgreSQL    | Relational database                   |
| SQL           | Database operations                   |
| Pytest        | Automated testing                     |
| python-dotenv | Environment configuration             |
| Git / GitHub  | Version control and source management |

## 🏗️ Application Structure

```text
food-redistribution-platform/
├── app.py                      Streamlit website (pages for each role)
├── app/
│   ├── auth.py                 Google login, access requests
│   ├── backend.py              Functions the pages call
│   ├── config.py               Settings from env / .env / Streamlit secrets
│   ├── database.py             Connection pool, India timezone
│   ├── schema.py               Creates and updates tables
│   ├── timeutil.py             One clock for the whole app
│   ├── user_service.py         Users, roles, approvals
│   ├── donation_service.py
│   ├── food_risk_service.py
│   ├── organization_service.py
│   ├── pickup_service.py
│   ├── restaurant_service.py
│   ├── volunteer_service.py
│   └── main.py                 Optional FastAPI version (not deployed)
├── tests/                      Automated tests (pytest)
├── .streamlit/secrets.toml.example
├── create_tables.py
├── insert_sample_data.py
├── requirements.txt            Website
├── requirements-api.txt        Optional FastAPI
└── requirements-dev.txt        Tests
```

## 🔄 Business Workflow

### 1. Restaurant creates a donation

A restaurant provides information about surplus food, including the relevant donation details.

The donation initially becomes available for processing.

```text
Restaurant
     ↓
Create Donation
     ↓
Donation = AVAILABLE
```

### 2. Organization verification

Organizations are maintained with verification information.

Only eligible/verified organizations can participate in the pickup workflow.

```text
Organization
     ↓
Verification
     ↓
VERIFIED / ACTIVE
```

### 3. Organization requests a pickup

A verified organization can request an available donation.

The system validates whether the donation is eligible before creating the pickup request.

```text
AVAILABLE Donation
        ↓
Pickup Request
        ↓
REQUESTED
```

### 4. Volunteer assignment

An available volunteer can be assigned to an eligible pickup request.

The volunteer status is updated accordingly.

```text
REQUESTED
    ↓
Volunteer Assignment
    ↓
ACCEPTED
```

### 5. Food pickup

Once the volunteer collects the donation, the pickup and donation statuses are updated.

```text
Pickup
  ↓
PICKED_UP

Donation
  ↓
PICKED_UP
```

### 6. Delivery

After the food reaches the organization:

```text
Pickup
  ↓
DELIVERED

Donation
  ↓
DELIVERED
```

This provides end-to-end tracking of the donation lifecycle.

## 📊 Status Management

### Donation Status

```text
AVAILABLE
    ↓
RESERVED
    ↓
PICKED_UP
    ↓
DELIVERED
```

### Pickup Status

```text
REQUESTED
    ↓
ACCEPTED
    ↓
PICKED_UP
    ↓
DELIVERED
```

### Volunteer Status

```text
ACTIVE
  ↓
BUSY
  ↓
ACTIVE
```

The volunteer becomes unavailable while handling an active pickup and can become available again after completing the assignment.

## 🧩 Service Layer

The application separates business functionality into dedicated service modules.

### `donation_service.py`

Handles donation-related operations and validation.

### `restaurant_service.py`

Handles restaurant-related operations.

### `organization_service.py`

Handles organization registration, verification, and related business operations.

### `pickup_service.py`

Handles pickup requests, pickup status changes, and pickup workflow.

### `volunteer_service.py`

Handles volunteer assignment and volunteer status management.

### `food_risk_service.py`

Contains food-related validation/risk logic used to identify potentially problematic donation scenarios.

### `database.py`

Provides database connectivity and database-related functionality.

This separation keeps the business logic modular and easier to maintain and test.

## 🗄️ Database

The application uses **PostgreSQL**. The live app uses a free [Neon](https://neon.com) database (permanent free plan, no credit card).

Tables: restaurants, food_donations, organizations, volunteers, pickup_requests, and app_users (who may log in, and in which role).

Tables are created automatically when the app starts (`app/schema.py`). This is safe to repeat: it only adds what is missing and never deletes data.

## 🏗️ How the app is deployed

```text
Browser ──► Streamlit app (Streamlit Community Cloud)
              │  app.py  ─►  app/backend.py  ─►  app/*_service.py
              ▼
           PostgreSQL (Neon)
```

The Streamlit app calls the service functions directly. There is no separate API server to keep awake, so there are no "Read timed out" errors and no public API exposing data.

The FastAPI version (`app/main.py`) still works for learning or for a future mobile app. It has **no login**, so do not deploy it publicly as it is. Run it with `pip install -r requirements-api.txt` and `uvicorn app.main:app --reload`.

## 🔐 Login and roles

People sign in with Google (Streamlit's built-in `st.login()`). Each person has one role:

| Role | Who | Can |
| --- | --- | --- |
| Admin | Ministry coordinators | Everything: approve people, verify organizations, accept pickups, assign volunteers |
| Donor | Restaurant, caterer, family | Register their kitchen; post food donations |
| Organization | NGO, home, charity | Register; once verified, see available food and request pickups for themselves |
| Volunteer | Drivers and helpers | See only pickups assigned to them; mark picked up and delivered |

A new person signs in, picks a role, and waits; an admin approves them under **User Access**. Emails listed in `ADMIN_EMAILS` become admins automatically. Phone numbers and addresses of volunteers and others are visible to admins only.

## 🧪 Testing

41 automated tests cover donation validation, organization verification and rejection, the full pickup flow, duplicate and simultaneous pickup requests, India-time checks, volunteer assignment rules, user approval, and every page clicked through as each role (using Streamlit's `AppTest`).

The tests **empty every table**, so they need a separate, throw-away database:

```bash
pip install -r requirements-dev.txt
# PowerShell:  $env:TEST_DATABASE_URL="postgresql://postgres:PASSWORD@localhost:5432/food_test"
export TEST_DATABASE_URL="postgresql://postgres:PASSWORD@localhost:5432/food_test"
pytest
```

Without `TEST_DATABASE_URL` the tests are skipped, so they can never wipe the real database.

## ⚙️ Configuration

Settings come from environment variables, a local `.env` file, or Streamlit secrets. Nothing secret goes in the code or on GitHub. See `.streamlit/secrets.toml.example`.

| Setting | Meaning |
| --- | --- |
| `DATABASE_URL` | Postgres connection string (Neon "pooled" string). The older `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` also work. |
| `ADMIN_EMAILS` | Comma-separated emails that become admins |
| `APP_TIMEZONE` | Defaults to `Asia/Kolkata`; all times are entered and checked in this zone |
| `[auth]` section | Google sign-in (below) |
| `DEV_LOGIN=true` | **Local testing only**: sign in by typing an email instead of Google |

## ▶️ Running the Project Locally

```bash
git clone https://github.com/srilathasanga/food-redistribution-platform.git
cd food-redistribution-platform
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/food_redistribution
ADMIN_EMAILS=you@example.com
DEV_LOGIN=true
```

Then run `streamlit run app.py`, open http://localhost:8501 and sign in as `you@example.com`. Optional: `python insert_sample_data.py` adds demo data.

## 🚀 Deploying for free (Streamlit Cloud + Neon + Google login)

### 1. Create the database on Neon

1. Sign up at [neon.com](https://neon.com) with the **ministry's** Google account, and create a project (region: Asia Pacific, Singapore).
2. Click **Connect**, tick **Connection pooling**, and copy the connection string.
3. To bring across existing data from the old database, run `pg_dump --no-owner --no-acl "OLD_DATABASE_URL" > backup.sql` and then `psql "NEON_DATABASE_URL" < backup.sql`. Otherwise start empty: the app creates the tables.

### 2. Set up Google login

1. In [Google Cloud Console](https://console.cloud.google.com) (ministry account), create a project.
2. **APIs & Services → OAuth consent screen**: External, app name "Food Redistribution Platform", then **Publish app**.
3. **Credentials → Create credentials → OAuth client ID** → Web application. Under *Authorized redirect URIs* add `https://YOUR-APP.streamlit.app/oauth2callback` (and `http://localhost:8501/oauth2callback` for local testing).
4. Copy the client ID and secret.
5. Make a cookie secret: `python -c "import secrets; print(secrets.token_hex(32))"`.

### 3. Configure Streamlit Community Cloud

In the app's **Settings → Secrets**, paste the content of `.streamlit/secrets.toml.example` filled in with the real values (`DATABASE_URL`, `ADMIN_EMAILS`, and the `[auth]` section). Save, then reboot the app.

### 4. Retire the old server

Once the new version works, suspend or delete the old Render web service and database. The old FastAPI service has no login, so it should not stay online.

### 5. Back up

Run a monthly backup: `pg_dump --no-owner --no-acl "NEON_DATABASE_URL" > backup-YYYY-MM.sql`, and keep it in the ministry's Google Drive.

## 🧪 Example End-to-End Scenario

A typical successful workflow looks like:

```text
Restaurant
   │
   │ Creates food donation
   ▼
Food Donation
   │
   │ Donation available
   ▼
Verified Organization
   │
   │ Creates pickup request
   ▼
Pickup Request
   │
   │ Volunteer assigned
   ▼
Volunteer
   │
   │ Picks up food
   ▼
Food Picked Up
   │
   │ Delivers to organization
   ▼
Food Delivered
```

This workflow demonstrates how multiple business entities interact while maintaining consistent status transitions.

## 💡 What I Learned From This Project

This project helped me gain practical experience in:

* Python application development
* REST API development using FastAPI
* PostgreSQL database integration
* Service-layer architecture
* Business workflow implementation
* Status/state management
* Input validation
* Exception handling
* Automated testing with Pytest
* Streamlit application development
* Environment variable management
* Git and GitHub version control
* Designing an end-to-end real-world application

## 🚀 Future Enhancements

Potential future improvements include:

* Real-time volunteer notifications
* Location-based volunteer assignment
* Food expiry alerts
* Dashboard and analytics
* Docker containerization
* CI/CD pipeline
* Improved audit logging
* Integration with mapping/location services

## 👩‍💻 Project Purpose

This is a personal learning project created to explore the design and implementation of a complete Python-based application solving a real-world food redistribution problem.

The focus was not only on building individual APIs, but also on implementing a complete business workflow from **food donation creation through successful delivery**.
