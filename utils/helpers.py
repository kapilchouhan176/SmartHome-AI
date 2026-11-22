"""
utils/helpers.py
Small shared helpers used by routes and templates.
"""
from datetime import date, timedelta

from flask import url_for

from config import Config
from utils.database import fetch_one, fetch_all


# Turns a MySQL TIME value (returned as timedelta) into "HH:MM" text.
def format_slot(value):
    if isinstance(value, timedelta):
        minutes = int(value.total_seconds()) // 60
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    return str(value)[:5]


# Formats a number as Indian rupees, e.g. 1499 -> "₹1,499".
def format_inr(value):
    return f"₹{float(value or 0):,.0f}"


# Returns the dashboard URL for a role: customer, provider or admin.
def dashboard_url(role):
    return url_for(f"{role}.dashboard")


# Returns the first and last date a customer is allowed to book.
def booking_date_range():
    today = date.today()
    return today, today + timedelta(days=Config.BOOKING_DAYS_AHEAD)


# Returns the providers row that belongs to a user (or None).
def get_provider_by_user(user_id):
    return fetch_one("SELECT * FROM providers WHERE user_id = %s", (user_id,))


# Returns all active service categories, sorted by name.
def get_active_services():
    return fetch_all("SELECT * FROM services WHERE is_active = 1 ORDER BY name")


# Returns one active service by id (or None).
def get_active_service(service_id):
    return fetch_one("SELECT * FROM services WHERE id = %s AND is_active = 1", (service_id,))


# Returns a safe local redirect target, ignoring links to other websites.
def safe_next_url(target):
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None
