"""
routes/provider.py
Provider dashboard, profile, offered services and reviews.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, session

from services.booking_service import provider_bookings
from utils.database import fetch_one, fetch_all, execute, commit
from utils.decorators import role_required
from utils.helpers import get_provider_by_user, get_active_service
from utils.validators import is_valid_phone, missing_fields, parse_charge, parse_experience

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")


# Returns the logged-in provider's providers row (404 if missing).
def current_provider():
    provider = get_provider_by_user(g.user["id"])
    if provider is None:
        abort(404)
    return provider


# Dashboard: stats, new requests, active jobs and past jobs.
@provider_bp.route("/dashboard")
@role_required("provider")
def dashboard():
    provider = current_provider()
    bookings = provider_bookings(provider["id"])
    groups = {
        "requests": [b for b in bookings if b["status"] == "pending"],
        "active": [b for b in bookings if b["status"] in ("accepted", "in_progress")],
        "history": [b for b in bookings if b["status"] in ("completed", "rejected", "cancelled")],
    }
    return render_template("provider/dashboard.html", provider=provider,
                           stats=build_stats(bookings, provider), **groups)


# Totals shown in the provider's stat cards.
def build_stats(bookings, provider):
    completed = [b for b in bookings if b["status"] == "completed"]
    return {
        "total": len(bookings),
        "pending": sum(b["status"] == "pending" for b in bookings),
        "completed": len(completed),
        "earnings": sum(float(b["estimated_cost"]) for b in completed),
        "rating": float(provider["avg_rating"]),
        "reviews": provider["total_reviews"],
    }


# Shows and saves the provider's personal and work details.
@provider_bp.route("/profile", methods=["GET", "POST"])
@role_required("provider")
def profile():
    provider = current_provider()
    if request.method == "POST" and save_profile(request.form, provider["id"]):
        flash("Profile updated.", "success")
        return redirect(url_for("provider.profile"))
    user = fetch_one("SELECT * FROM users WHERE id = %s", (g.user["id"],))
    return render_template("provider/profile.html", user=user, provider=provider)


# Validates the profile form and updates users + providers. Returns True on success.
def save_profile(form, provider_id):
    errors = missing_fields(form, {"name": "Name", "phone": "Phone", "city": "City"})
    experience = parse_experience(form.get("experience_years"))
    if form.get("phone") and not is_valid_phone(form["phone"].strip()):
        errors.append("Phone number must be exactly 10 digits.")
    if experience is None:
        errors.append("Experience must be a whole number between 0 and 60.")
    for error in errors:
        flash(error, "danger")
    if errors:
        return False
    city = form["city"].strip()
    execute("UPDATE users SET name = %s, phone = %s, city = %s WHERE id = %s",
            (form["name"].strip(), form["phone"].strip(), city, g.user["id"]), commit=False)
    execute("UPDATE providers SET bio = %s, experience_years = %s, city = %s, is_available = %s WHERE id = %s",
            (form.get("bio", "").strip() or None, experience, city,
             1 if form.get("is_available") else 0, provider_id), commit=False)
    commit()
    session["name"] = form["name"].strip()
    return True


# Lists offered services and a form to add a new one.
@provider_bp.route("/services")
@role_required("provider")
def services():
    provider = current_provider()
    offered = fetch_all(
        """SELECT ps.id, ps.charge, s.name, s.icon, s.base_price, s.is_active
           FROM provider_services ps JOIN services s ON s.id = ps.service_id
           WHERE ps.provider_id = %s ORDER BY s.name""",
        (provider["id"],),
    )
    available = fetch_all(
        """SELECT * FROM services WHERE is_active = 1 AND id NOT IN
           (SELECT service_id FROM provider_services WHERE provider_id = %s) ORDER BY name""",
        (provider["id"],),
    )
    return render_template("provider/services.html", offered=offered, available=available)


# Adds a service with the provider's own charge (or updates the charge).
@provider_bp.route("/services/add", methods=["POST"])
@role_required("provider")
def add_service():
    provider = current_provider()
    service = get_active_service(request.form.get("service_id", type=int))
    charge = parse_charge(request.form.get("charge"))
    if service is None or charge is None:
        flash("Please choose a service and enter a positive charge.", "danger")
    else:
        execute(
            """INSERT INTO provider_services (provider_id, service_id, charge) VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE charge = VALUES(charge)""",
            (provider["id"], service["id"], charge),
        )
        flash(f"{service['name']} saved at ₹{charge:,.0f}.", "success")
    return redirect(url_for("provider.services"))


# Removes a service, but only if it belongs to this provider.
@provider_bp.route("/services/<int:offer_id>/remove", methods=["POST"])
@role_required("provider")
def remove_service(offer_id):
    provider = current_provider()
    execute("DELETE FROM provider_services WHERE id = %s AND provider_id = %s", (offer_id, provider["id"]))
    flash("Service removed.", "info")
    return redirect(url_for("provider.services"))


# Lists reviews customers left for this provider.
@provider_bp.route("/reviews")
@role_required("provider")
def reviews():
    provider = current_provider()
    rows = fetch_all(
        """SELECT r.*, u.name AS customer_name, s.name AS service_name
           FROM reviews r JOIN users u ON u.id = r.customer_id
           JOIN bookings b ON b.id = r.booking_id JOIN services s ON s.id = b.service_id
           WHERE r.provider_id = %s ORDER BY r.created_at DESC""",
        (provider["id"],),
    )
    return render_template("provider/reviews.html", provider=provider, reviews=rows)
