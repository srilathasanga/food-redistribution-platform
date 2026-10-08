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
| FastAPI       | REST API backend                      |
| Streamlit     | User interface                        |
| PostgreSQL    | Relational database                   |
| SQL           | Database operations                   |
| Pytest        | Automated testing                     |
| python-dotenv | Environment configuration             |
| Git / GitHub  | Version control and source management |

## 🏗️ Application Structure

```text
food_redistribution/
│
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── donation_service.py
│   ├── food_risk_service.py
│   ├── organization_service.py
│   ├── pickup_service.py
│   ├── restaurant_service.py
│   └── volunteer_service.py
│
├── tests/
│   ├── test_assign_volunteer.py
│   ├── test_complete_flow.py
│   ├── test_db.py
│   ├── test_donation_pickup_flow.py
│   ├── test_donation_service.py
│   ├── test_donation_validation.py
│   ├── test_duplicate_pickup.py
│   ├── test_organization_service.py
│   ├── test_pickup_service.py
│   ├── test_pickup_status.py
│   ├── test_restaurant_service.py
│   └── test_volunteer_service.py
│
├── app.py
├── main.py
├── create_tables.py
├── insert_sample_data.py
├── test_database.py
├── requirements.txt
└── README.md
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

The application uses **PostgreSQL** for persistent data storage.

The platform works with entities such as:

* Restaurants
* Food Donations
* Organizations
* Pickup Requests
* Volunteers

The relationships between these entities allow the application to maintain the complete donation-to-delivery workflow.

## 🔌 Backend

The backend is implemented using **FastAPI**.

FastAPI provides API endpoints for interacting with the application and supports automatic API documentation.

The application can be explored through FastAPI's interactive documentation when the backend is running.

## 🖥️ Frontend

A **Streamlit** interface is used to provide a simple user-facing application for interacting with the platform.

This allows the project to demonstrate both:

* Backend API development
* User interface integration

## 🧪 Testing

The project includes automated tests covering important business scenarios.

Examples include:

* Database connectivity
* Donation creation
* Donation validation
* Restaurant operations
* Organization operations
* Pickup creation
* Duplicate pickup validation
* Pickup status transitions
* Volunteer assignment
* Volunteer operations
* Complete donation/pickup flow

Tests are maintained separately under the `tests/` directory.

Run the test suite using:

```bash
pytest
```

## ⚙️ Configuration

Environment-specific configuration is maintained using environment variables.

Sensitive configuration such as database credentials should be stored in a local `.env` file.

Example:

```env
DATABASE_URL=your_database_connection_string
```

**Do not commit the `.env` file to GitHub.**

## ▶️ Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/srilathasanga/food-redistribution-platform.git
cd food-redistribution-platform
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file and provide the required PostgreSQL/database configuration.

### 6. Create database tables

```bash
python create_tables.py
```

### 7. Insert sample data

```bash
python insert_sample_data.py
```

### 8. Start the FastAPI application

Depending on the configured entry point:

```bash
uvicorn main:app --reload
```

FastAPI documentation will normally be available at:

```text
http://127.0.0.1:8000/docs
```

### 9. Start the Streamlit application

```bash
streamlit run app.py
```

The Streamlit application will normally be available at:

```text
http://localhost:8501
```

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

* Authentication and role-based authorization
* Real-time volunteer notifications
* Location-based volunteer assignment
* Food expiry alerts
* Dashboard and analytics
* Docker containerization
* Cloud deployment
* CI/CD pipeline
* Improved audit logging
* Integration with mapping/location services

## 👩‍💻 Project Purpose

This is a personal learning project created to explore the design and implementation of a complete Python-based application solving a real-world food redistribution problem.

The focus was not only on building individual APIs, but also on implementing a complete business workflow from **food donation creation through successful delivery**.
