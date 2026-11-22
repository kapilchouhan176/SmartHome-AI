"""
routes/customer.py
Customer dashboard and profile.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, session

from services.booking_service import customer_bookings
from services.dashboard_service import popular_services, top_providers, recommendations
from services.notification_service import get_notifications
from utils.database import fetch_one, execute
from utils.decorators import role_required
from utils.validators import is_valid_phone, missing_fields

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

ACTIVE_STATUSES = ("pending", "accepted", "in_progress")


# Dashboard: stats, upcoming bookings, notifications, and city-based
# suggestions (popular services, top providers, recommendations).
@customer_bp.route("/dashboard")
@role_required("customer")
def dashboard():
    bookings = customer_bookings(g.user["id"])
    city = g.user["city"] or ""
    return render_template(
        "customer/dashboard.html", city=city, stats=count_by_status(bookings),
        upcoming=[b for b in bookings if b["status"] in ACTIVE_STATUSES],
        notifications=get_notifications(g.user["id"], limit=5),
        popular=popular_services(city), providers=top_providers(city),
        recommended=recommendations(bookings),
    )


# Counts bookings in each status group for the stat cards.
def count_by_status(bookings):
    return {
        "total": len(bookings),
        "active": sum(b["status"] in ACTIVE_STATUSES for b in bookings),
        "completed": sum(b["status"] == "completed" for b in bookings),
        "cancelled": sum(b["status"] in ("cancelled", "rejected") for b in bookings),
    }


# Shows and saves the customer's name, phone, city and address.
@customer_bp.route("/profile", methods=["GET", "POST"])
@role_required("customer")
def profile():
    if request.method == "POST":
        if save_profile(request.form):
            flash("Profile updated.", "success")
            return redirect(url_for("customer.profile"))
    user = fetch_one("SELECT * FROM users WHERE id = %s", (g.user["id"],))
    return render_template("customer/profile.html", user=user)


# Validates and saves the profile form. Returns True on success.
def save_profile(form):
    errors = missing_fields(form, {"name": "Name", "phone": "Phone", "city": "City"})
    if form.get("phone") and not is_valid_phone(form["phone"].strip()):
        errors.append("Phone number must be exactly 10 digits.")
    for error in errors:
        flash(error, "danger")
    if errors:
        return False
    execute("UPDATE users SET name = %s, phone = %s, city = %s, address = %s WHERE id = %s",
            (form["name"].strip(), form["phone"].strip(), form["city"].strip(),
             form.get("address", "").strip() or None, g.user["id"]))
    session["name"] = form["name"].strip()
    return True
