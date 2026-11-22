"""
services/cost_estimator.py
Simple rule-based price estimate. This is plain arithmetic, NOT AI.
"""
from config import Config


# Adds the urgent fee (if any) to the base charge.
# Returns a dict with base, urgent and total amounts in ₹.
def estimate(base_charge, is_urgent):
    base = round(float(base_charge), 2)
    urgent = float(Config.URGENT_CHARGE) if is_urgent else 0.0
    return {"base": base, "urgent": urgent, "total": round(base + urgent, 2)}
