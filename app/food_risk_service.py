
from datetime import datetime

from app.database import get_connection

# from app.food_risk_service import get_food_risk_analysis



# =========================================================
# FOOD RISK CALCULATION
# =========================================================

def calculate_food_risk(expiry_time):

    now = datetime.now()

    time_remaining = expiry_time - now

    hours_remaining = time_remaining.total_seconds() / 3600

    if hours_remaining <= 0:

        risk_level = "EXPIRED"
        risk_score = 100
        priority = "NO ACTION - EXPIRED"

        reasons = [
            "The donation has already passed its expiry time."
        ]

    elif hours_remaining < 2:

        risk_level = "HIGH"
        risk_score = 80
        priority = "URGENT"

        reasons = [
            "Less than 2 hours remain before expiry.",
            "Immediate redistribution should be considered."
        ]

    elif hours_remaining <= 6:

        risk_level = "MEDIUM"
        risk_score = 50
        priority = "HIGH PRIORITY"

        reasons = [
            "Between 2 and 6 hours remain before expiry.",
            "The donation should be prioritized for redistribution."
        ]

    else:

        risk_level = "LOW"
        risk_score = 20
        priority = "NORMAL"

        reasons = [
            "More than 6 hours remain before expiry.",
            "There is sufficient time for normal redistribution."
        ]

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "hours_remaining": round(hours_remaining, 2),
        "priority": priority,
        "reasons": reasons
    }
## Recomended operational function ##

def get_recommended_action(risk_level, donation_status):

    if donation_status == "DELIVERED":
        return "No action required - donation already delivered."

    if donation_status == "PICKED_UP":
        return "Pickup completed - delivery is in progress."

    if risk_level == "EXPIRED":
        return "Do not redistribute - donation has expired."

    if risk_level == "HIGH":
        return "Assign volunteer immediately and prioritize pickup."

    if risk_level == "MEDIUM":
        return "Prioritize this donation for pickup."

    if risk_level == "LOW":
        return "Continue normal redistribution process."

    return "Review donation manually."


# =========================================================
# GET DONATIONS FROM DATABASE
# =========================================================

def get_donations_for_risk_analysis():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                donation_id,
                food_name,
                quantity,
                unit,
                expiry_time,
                donation_status,
                packaging_status
            FROM food_donations
            ORDER BY donation_id;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


# =========================================================
# FOOD RISK ANALYSIS
# =========================================================

def get_food_risk_analysis():

    donations = get_donations_for_risk_analysis()

    risk_results = []

    for donation in donations:

        donation_id = donation[0]
        food_name = donation[1]
        quantity = donation[2]
        unit = donation[3]
        expiry_time = donation[4]
        donation_status = donation[5]
        packaging_status = donation[6]

        # Only analyze donations that still
        # need operational attention.
        if donation_status not in ["AVAILABLE", "RESERVED"]:
            continue

        risk = calculate_food_risk(expiry_time)

        risk_results.append({
            "donation_id": donation_id,
            "food_name": food_name,
            "quantity": float(quantity),
            "unit": unit,
            "expiry_time": expiry_time,
            "donation_status": donation_status,
            "packaging_status": packaging_status,

            # Risk information
            "risk_level": risk["risk_level"],
            "risk_score": risk["risk_score"],
            "hours_remaining": risk["hours_remaining"],
            "priority": risk["priority"],
            "recommended_action": get_recommended_action(
                risk["risk_level"],
                donation_status
            ),
            "reasons": risk["reasons"]
        })

    return risk_results

