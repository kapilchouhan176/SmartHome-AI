"""
routes/admin.py
Admin pages: stats, provider verification, service categories,
users, all bookings, all reviews.
"""
import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from ai_models.demand_forecast import demand_summary
from services.notification_service import notify
from utils.database import fetch_one, fetch_all, execute, commit
from utils.decorators import role_required
from utils.validators import missing_fields, parse_charge

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

BOOKING_STATUSES = ("pending", "accepted", "rejected", "in_progress", "completed", "cancelled")


# Dashboard with user, booking and AI statistics.
@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html", counts=user_counts(),
                           booking_counts=booking_counts(), ai=ai_stats())


# Number of customers, and verified/pending providers.
def user_counts():
    return fetch_one(
        """SELECT
             (SELECT COUNT(*) FROM users WHERE role = 'customer') AS customers,
             (SELECT COUNT(*) FROM providers) AS providers,
             (SELECT COUNT(*) FROM providers WHERE verification_status = 'verified') AS verified,
             (SELECT COUNT(*) FROM providers WHERE verification_status = 'pending') AS pending,
             (SELECT COUNT(*) FROM bookings) AS bookings"""
    )


# Bookings per status, including statuses with zero bookings.
def booking_counts():
    rows = fetch_all("SELECT status, COUNT(*) AS total FROM bookings GROUP BY status")
    found = {row["status"]: row["total"] for row in rows}
    return {status: found.get(status, 0) for status in BOOKING_STATUSES}


# Prediction count per service and review sentiment counts.
def ai_stats():
    predictions = fetch_all(
        """SELECT s.name, COUNT(a.id) AS total FROM services s
           LEFT JOIN ai_predictions a ON a.predicted_service_id = s.id
           GROUP BY s.id, s.name ORDER BY total DESC, s.name"""
    )
    rows = fetch_all("SELECT sentiment, COUNT(*) AS total FROM reviews GROUP BY sentiment")
    found = {row["sentiment"] or "not analysed": row["total"] for row in rows}
    sentiments = {key: found.get(key, 0) for key in ("positive", "neutral", "negative", "not analysed")}
    return {"predictions": predictions, "sentiments": sentiments}


# Demand page: weekday heatmap and next-week booking forecast.
@admin_bp.route("/demand")
@role_required("admin")
def demand():
    services = fetch_all("SELECT id, name, icon FROM services WHERE is_active = 1 ORDER BY name")
    return render_template("admin/demand.html", demand=demand_summary(services))


# Lists providers filtered by verification status (default: pending).
@admin_bp.route("/providers")
@role_required("admin")
def providers():
    status = request.args.get("status", "pending")
    if status not in ("pending", "verified", "rejected", "all"):
        status = "pending"
    sql = """SELECT p.*, u.name, u.email, u.phone, u.is_active,
                    (SELECT COUNT(*) FROM provider_services ps WHERE ps.provider_id = p.id) AS service_count
             FROM providers p JOIN users u ON u.id = p.user_id"""
    if status == "all":
        rows = fetch_all(sql + " ORDER BY p.created_at DESC")
    else:
        rows = fetch_all(sql + " WHERE p.verification_status = %s ORDER BY p.created_at DESC", (status,))
    return render_template("admin/providers.html", providers=rows, status=status)


# Approves or rejects a provider and notifies them.
@admin_bp.route("/providers/<int:provider_id>/status", methods=["POST"])
@role_required("admin")
def set_provider_status(provider_id):
    new_status = request.form.get("status")
    provider = fetch_one("SELECT * FROM providers WHERE id = %s", (provider_id,))
    if provider is None or new_status not in ("verified", "rejected"):
        abort(400)
    execute("UPDATE providers SET verification_status = %s WHERE id = %s",
            (new_status, provider_id), commit=False)
    notify(provider["user_id"], f"Your provider account has been {new_status} by the admin.",
           url_for("provider.dashboard"), commit=False)
    commit()
    flash(f"Provider {new_status}.", "success")
    return redirect(request.referrer or url_for("admin.providers"))


# Lists all service categories with a form to add a new one.
@admin_bp.route("/services", methods=["GET", "POST"])
@role_required("admin")
def services():
    if request.method == "POST" and save_service(request.form):
        flash("Service added.", "success")
        return redirect(url_for("admin.services"))
    rows = fetch_all("SELECT * FROM services ORDER BY name")
    return render_template("admin/services.html", services=rows)


# Edits one service category.
@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_service(service_id):
    service = fetch_one("SELECT * FROM services WHERE id = %s", (service_id,))
    if service is None:
        abort(404)
    if request.method == "POST" and save_service(request.form, service_id):
        flash("Service updated.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_edit.html", service=service)


# Validates and inserts (or updates, if service_id is given) a service.
def save_service(form, service_id=None):
    errors = missing_fields(form, {"name": "Name", "base_price": "Base price"})
    price = parse_charge(form.get("base_price"))
    if form.get("base_price") and price is None:
        errors.append("Base price must be a positive number.")
    for error in errors:
        flash(error, "danger")
    if errors:
        return False
    values = (form["name"].strip(), form.get("description", "").strip() or None,
              form.get("icon", "").strip() or "bi-tools", price)
    try:
        if service_id:
            execute("UPDATE services SET name=%s, description=%s, icon=%s, base_price=%s WHERE id=%s",
                    values + (service_id,))
        else:
            execute("INSERT INTO services (name, description, icon, base_price) VALUES (%s, %s, %s, %s)", values)
    except mysql.connector.IntegrityError:
        flash("A service with this name already exists.", "danger")
        return False
    return True


# Activates or deactivates a service category.
@admin_bp.route("/services/<int:service_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_service(service_id):
    execute("UPDATE services SET is_active = NOT is_active WHERE id = %s", (service_id,))
    flash("Service status changed.", "success")
    return redirect(url_for("admin.services"))


# Lists customers and providers, optionally filtered by role.
@admin_bp.route("/users")
@role_required("admin")
def users():
    role = request.args.get("role", "all")
    if role in ("customer", "provider", "admin"):
        rows = fetch_all("SELECT * FROM users WHERE role = %s ORDER BY created_at DESC", (role,))
    else:
        role = "all"
        rows = fetch_all("SELECT * FROM users ORDER BY created_at DESC")
    return render_template("admin/users.html", users=rows, role=role)


# Activates or deactivates a user (admins cannot be deactivated here).
@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_user(user_id):
    user = fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    if user is None or user["role"] == "admin":
        flash("Admin accounts can't be deactivated here.", "warning")
    else:
        execute("UPDATE users SET is_active = NOT is_active WHERE id = %s", (user_id,))
        flash(f"{user['name']} has been {'deactivated' if user['is_active'] else 'activated'}.", "success")
    return redirect(request.referrer or url_for("admin.users"))


# Lists every booking, optionally filtered by status.
@admin_bp.route("/bookings")
@role_required("admin")
def bookings():
    status = request.args.get("status", "all")
    sql = """SELECT b.*, s.name AS service_name, cu.name AS customer_name, pu.name AS provider_name
             FROM bookings b JOIN services s ON s.id = b.service_id
             JOIN users cu ON cu.id = b.customer_id
             JOIN providers p ON p.id = b.provider_id JOIN users pu ON pu.id = p.user_id"""
    if status in BOOKING_STATUSES:
        rows = fetch_all(sql + " WHERE b.status = %s ORDER BY b.booking_date DESC", (status,))
    else:
        status = "all"
        rows = fetch_all(sql + " ORDER BY b.booking_date DESC")
    return render_template("admin/bookings.html", bookings=rows, status=status, statuses=BOOKING_STATUSES)


# Lists every review with its AI sentiment.
@admin_bp.route("/reviews")
@role_required("admin")
def reviews():
    rows = fetch_all(
        """SELECT r.*, cu.name AS customer_name, pu.name AS provider_name
           FROM reviews r JOIN users cu ON cu.id = r.customer_id
           JOIN providers p ON p.id = r.provider_id JOIN users pu ON pu.id = p.user_id
           ORDER BY r.created_at DESC"""
    )
    return render_template("admin/reviews.html", reviews=rows)
