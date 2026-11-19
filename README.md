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
├── app.py                      Website set-up, sign-in and the menu (small)
├── app/
│   ├── screens/                One file per group of pages
│   │   ├── kitchens.py         My restaurant (donor), Restaurants (admin)
│   │   ├── organizations.py    My organization, Organizations (verify)
│   │   ├── food.py             Share food / My donations, Available food
│   │   ├── pickups.py          Pickup requests / My pickups
│   │   ├── people.py           Volunteers, User access
│   │   └── reports.py          Reports & tools
│   ├── home_pages.py           Home page for each role
│   ├── navigation.py           Which role sees which page (one list)
│   ├── ui.py                   Shared look: banner, cards, badges, CSS
│   ├── privacy.py              Public privacy policy page
│   ├── auth.py                 Google login, access requests
│   ├── backend.py              Functions the pages call
│   ├── config.py               Settings from env / .env / Streamlit secrets
│   ├── database.py             Connection pool, India timezone
│   ├── schema.py               Creates and updates tables
│   ├── timeutil.py             One clock for the whole app
│   ├── user_service.py         Users, roles, approvals
│   ├── donation_service.py     ┐
│   ├── food_risk_service.py    │
│   ├── organization_service.py │ Business rules and SQL
│   ├── pickup_service.py       │
│   ├── restaurant_service.py   │
│   ├── volunteer_service.py    ┘
│   └── main.py                 Optional FastAPI version (not deployed)
├── tests/                      Automated tests (pytest)
├── dev/ui_preview.py           Design preview with sample data (no database)
├── .streamlit/config.toml      Colours, fonts and sizes (the theme)
├── .streamlit/secrets.toml.example
├── create_tables.py
├── insert_sample_data.py
├── requirements.txt            Website
├── requirements-api.txt        Optional FastAPI
└── requirements-dev.txt        Tests
```

### Look and feel

- **Theme** (`.streamlit/config.toml`): royal blue `#364FC7` for buttons
  and links, coral accents, Poppins headings and Nunito Sans body text
  at 18px, rounded corners. Every text/background pair meets WCAG AA
  contrast; the reasons for each colour are written in the file.
- **Building blocks** (`app/ui.py`): `page_header` (blue banner),
  `card`, `stat_card`, `badge_markdown` (status words + icon, never
  colour alone), `empty_state`, `grid` (keeps cards in order on phones),
  `status_chart`, `friendly_time` ("in 45 min"). All custom CSS lives in
  this one file.
- **Phones first**: checked at 390px wide: no sideways scrolling, no
  text under 15px, tap targets at least 24px (most 40px+).
- See every building block with sample data, no database needed:
  `streamlit run dev/ui_preview.py`.

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

> **Running the app day to day?** See [HANDOVER.md](HANDOVER.md): what the owner manages, everyday tasks, what to do if something breaks, and the monthly backup.

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
| Admin | Ministry coordinators | Everything: approve people (**User access**), verify organizations (**Organizations**), accept pickups and assign volunteers (**Pickup requests**), add volunteers (**Volunteers**), see **Reports & tools** |
| Donor | Restaurant, caterer, family | Register their kitchen; share surplus food; follow their donations |
| Organization | NGO, home, charity | Register; once verified, request available food and follow their requests |
| Volunteer | Drivers and helpers | See only pickups assigned to them; mark picked up and delivered |

The menu for each role is listed in one place, `app/navigation.py`. A page that is not in a role's list cannot be opened, even by typing its address.

A new person signs in, picks a role, and waits; an admin approves them under **User access**. Emails listed in `ADMIN_EMAILS` become admins automatically.

Contact details of others are for admins only, with one exception: a volunteer sees the delivery address and contact of the organization **only for their own active pickups**. This is enforced in the database query (`get_volunteer_pickups` in `app/pickup_service.py`), not just hidden on screen. A volunteer has one active pickup at a time.

### Who can sign in: adding people

The Google sign-in is published (**In production**). Anyone can sign in with Google. New people are approved by the ministry admin before they can use the app.

1. A new person opens the app and signs in with their Google account.
2. They tell us their name, phone, city and how they want to help (donor, organization or volunteer). Until approved they only see a "thanks, please wait" screen.
3. An admin approves them under **User access** (or switches access off later).

Admins listed in `ADMIN_EMAILS` are approved automatically. Nobody needs to be added in Google Cloud any more.

### Privacy policy

The app has a public privacy policy at **`https://YOUR-APP.streamlit.app/?page=privacy`** (on your computer: http://localhost:8501/?page=privacy). It needs no sign-in and works even when the database is down. It is linked from the sign-in screen and the sidebar.

- Paste that address into Google Cloud → **Google Auth Platform → Branding → Privacy policy link**.
- To change the text, ministry name or contact, edit `app/privacy.py` (`MINISTRY_NAME` and `PRIVACY_POLICY`), and update the date.

## 🧪 Testing

About 60 automated tests cover donation validation, organization verification and rejection, the full pickup flow, duplicate and simultaneous pickup requests, India-time checks, volunteer assignment rules and what volunteers may see, user approval, which role sees which page, and every page clicked through as each role (using Streamlit's `AppTest`).

The tests **empty every table**, so they need a separate, throw-away database: a local Postgres database, or a free Neon **branch** made only for testing.

```powershell
pip install -r requirements-dev.txt
$env:TEST_DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"   # test database ONLY
python -m pytest      # "pytest" alone may be blocked by Windows Application Control
```

- Set `TEST_DATABASE_URL` **in the same terminal** where you run `pytest`.
- Without `TEST_DATABASE_URL`, the database tests are skipped (the others still run).

> ⚠️ **Safety: never point `TEST_DATABASE_URL` at the real database.**
> On a computer whose `.streamlit/secrets.toml` holds the real Neon address,
> Streamlit copies that address over `DATABASE_URL` the first time any secret
> is read. Before November 2026 this meant the tests could silently connect to
> the **real** database and empty it. Two protections now exist:
>
> 1. `app/config.py` keeps the settings that existed when the program started,
>    so `TEST_DATABASE_URL` wins over `secrets.toml`
>    (proved by `tests/test_settings_safety.py`).
> 2. Before creating or emptying anything, every database test checks the
>    **live connection**: its host and database name must match
>    `TEST_DATABASE_URL` and must **not** match the database in
>    `secrets.toml` (Neon's `-pooler` address counts as the same database).
>    Otherwise the whole run stops with "STOPPED to protect real data. No
>    table was emptied." (`tests/db_safety.py`, used by `tests/conftest.py`).
>
> Do not remove or weaken these checks.

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

> ⚠️ If this computer has a `.streamlit/secrets.toml` with the **real** Neon address, `streamlit run app.py` works on the **real** data: signing in, sharing food or approving people changes it. With `streamlit run`, **`secrets.toml` wins over `.env` and environment variables** (Streamlit reads it when the server starts). To experiment safely, rename `secrets.toml` to `secrets.toml.off` and put a local or Neon test-branch `DATABASE_URL` in `.env`; rename it back afterwards. (Tests are different: under `pytest`, `TEST_DATABASE_URL` wins and is double-checked, see Testing.)

## 🚀 Deploying for free (Streamlit Cloud + Neon + Google login)

### 1. Create the database on Neon

1. Sign up at [neon.com](https://neon.com) with the **ministry's** Google account, and create a project (region: Asia Pacific, Singapore).
2. Click **Connect**, tick **Connection pooling**, and copy the connection string.
3. To bring across existing data from the old database, run `pg_dump --no-owner --no-acl "OLD_DATABASE_URL" > backup.sql` and then `psql "NEON_DATABASE_URL" < backup.sql`. Otherwise start empty: the app creates the tables.

### 2. Set up Google login

1. In [Google Cloud Console](https://console.cloud.google.com) (ministry account), create a project.
2. **Google Auth Platform → Branding**: app name "Food Redistribution Platform", support email, and **Privacy policy link** `https://YOUR-APP.streamlit.app/?page=privacy`.
3. **Google Auth Platform → Audience**: External, **published (In production)**, so anyone with a Google account can sign in; the app's own approval step decides who gets in (see "Who can sign in" above).
4. **Google Auth Platform → Clients → Create client** → Web application. Under *Authorized redirect URIs* add `https://YOUR-APP.streamlit.app/oauth2callback` (and `http://localhost:8501/oauth2callback` for local testing).
5. Copy the client ID and secret.
6. Make a cookie secret: `python -c "import secrets; print(secrets.token_hex(32))"`.

In the Streamlit secrets, `redirect_uri` must be the **live** address ending in `/oauth2callback` (the local `secrets.toml` uses `http://localhost:8501/oauth2callback`).

### 3. Configure Streamlit Community Cloud

In the app's **Settings → Secrets**, paste the content of `.streamlit/secrets.toml.example` filled in with the real values (`DATABASE_URL`, `ADMIN_EMAILS`, and the `[auth]` section). Save, then reboot the app.

### 4. Retire the old server

Once the new version works, suspend or delete the old Render web service and database. The old FastAPI service has no login, so it should not stay online.

### 5. Back up

Run a monthly backup and keep it in a private folder in the ministry's Google Drive: step by step in [HANDOVER.md](HANDOVER.md) (section e).

## ✅ Go-live checklist

Do these in order, on the day the pilot starts.

1. **Owner saves Streamlit Secrets.** In Streamlit Community Cloud → the app → **Settings → Secrets**, the app owner pastes the real values: `DATABASE_URL` (Neon, pooled), `ADMIN_EMAILS`, and the `[auth]` section with the **live** `redirect_uri` (`https://YOUR-APP.streamlit.app/oauth2callback`). Do **not** set `DEV_LOGIN`. Save.
2. **Clear test data in Neon.** First make a safety copy: in Neon, create a branch named `before-go-live` from the production branch. Then open the **SQL Editor on the production branch** and run, once:

   ```sql
   -- PRODUCTION, once, before go-live. Deletes ALL rows in these tables.
   TRUNCATE pickup_requests, food_donations, restaurants, organizations,
            volunteers, app_users RESTART IDENTITY CASCADE;
   ```

   Admins listed in `ADMIN_EMAILS` are created again automatically at their first sign-in; everyone else simply asks for access again.
3. **Merge and push.** Merge `stabilize-and-secure` into `main` (through the pull request) and push. Streamlit Cloud redeploys from `main`.
4. **Sign in and check.** On the live address: open `/?page=privacy` without signing in; sign in as an admin; let one new person sign in with Google and ask for access, and approve them; share one food item, request it, accept it, assign a volunteer, mark it picked up and delivered. On a phone too.
5. **Suspend Render.** Once the live app works, suspend (later delete) the old Render web service and database. The old FastAPI service has no login and must not stay online.

## 🧭 Known gaps

- **Some checks live only in the forms for now.** These are checked on screen but not yet in the services, so the optional FastAPI app (`app/main.py`) and direct service calls do not enforce them:
  - an organization must have an address;
  - shared food must have a quantity and a pickup address;
  - phone numbers must look like a 10-digit mobile number, and emails must contain `@`;
  - shared food cannot already be expired (the form only offers future times; `add_food_donation` only checks that expiry is after the prepared time).

  They should move into `app/*_service.py` (raising `ValueError`) with a test for each.
- A volunteer can have only one active pickup at a time (kept on purpose for the pilot).

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
