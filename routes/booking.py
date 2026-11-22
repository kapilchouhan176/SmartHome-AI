"""
routes/booking.py
Booking flow: compare providers, book a slot, view history,
change status, cancel and review.
"""
from datetime import date

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, jsonify

from ai_models import sentiment_analyzer
from ai_models.provider_recommender import rank_providers
from config import Config
from services import booking_service
from services.cost_estimator import estimate
from services.notification_service import notify
from utils.database import fetch_one, execute, commit, rollback
from utils.decorators import role_required, login_required
from utils.helpers import booking_date_range, get_active_service, get_provider_by_user
from utils.validators import validate_date_and_slot, is_past_slot, parse_date, parse_rating, missing_fields

booking_bp = Blueprint("booking", __name__, url_prefix="/bookings")


# Side-by-side comparison of 2-3 ranked providers for one service.
@booking_bp.route("/compare")
def compare():
    service = get_active_service(request.args.get("service_id", type=int))
    city = request.args.get("city", "").strip()
    chosen = set(request.args.getlist("provider_ids", type=int))
    if service is None or not 2 <= len(chosen) <= 3:
        flash("Please select 2 or 3 providers to compare.", "warning")
        return redirect(request.referrer or url_for("main.services"))
    providers = [p for p in rank_providers(service["id"], city) if p["id"] in chosen]
    return render_template("bookings/compare.html", service=service, city=city, providers=providers)


# Booking form for one provider + service; on POST, creates the booking.
@booking_bp.route("/new", methods=["GET", "POST"])
@role_required("customer")
def new():
    source = request.form if request.method == "POST" else request.args
    offer = booking_service.get_offer(source.get("provider_id", type=int), source.get("service_id", type=int))
    if offer is None:
        flash("This provider is not available for that service.", "warning")
        return redirect(url_for("main.services"))
    if request.method == "POST":
        booking_id = try_create_booking(request.form, offer)
        if booking_id:
            flash("Booking request sent! The provider will confirm soon.", "success")
            return redirect(url_for("booking.history"))
    return render_booking_form(offer, source)


# Renders the booking page with cost estimate, dates and slots.
def render_booking_form(offer, source):
    first, last = booking_date_range()
    chosen_date = parse_date(source.get("booking_date")) or first
    profile = fetch_one("SELECT city, address FROM users WHERE id = %s", (g.user["id"],))
    return render_template(
        "bookings/new.html", offer=offer, form=source, profile=profile,
        cost=estimate(offer["charge"], bool(source.get("is_urgent"))),
        urgent_charge=Config.URGENT_CHARGE, min_date=first, max_date=last,
        chosen_date=chosen_date, slots=slot_choices(offer["provider_id"], chosen_date),
    )


# Validates the form and inserts the booking. Returns the id or None.
def try_create_booking(form, offer):
    data, error = read_booking_form(form, offer)
    if error:
        flash(error, "danger")
        return None
    if data["slot"] in booking_service.booked_slots(offer["provider_id"], data["booking_date"]):
        flash("Sorry, that slot is already booked. Please pick another.", "danger")
        return None
    try:
        return booking_service.create_booking(data, offer)
    except mysql.connector.IntegrityError as err:
        rollback()
        if err.errno != 1062:
            raise
        flash("Sorry, that slot just got booked by someone else. Please pick another.", "danger")
        return None


# Reads and checks booking form fields. Returns (data, None) or (None, error).
def read_booking_form(form, offer):
    missing = missing_fields(form, {"address": "Address", "city": "City", "problem": "Problem description"})
    if missing:
        return None, missing[0]
    booking_date, error = validate_date_and_slot(form.get("booking_date"), form.get("time_slot"))
    if error:
        return None, error
    if form["city"].strip().lower() != offer["city"].lower():
        return None, f"This provider only works in {offer['city']}."
    is_urgent = bool(form.get("is_urgent"))
    return {
        "customer_id": g.user["id"], "booking_date": booking_date, "slot": form["time_slot"],
        "address": form["address"].strip()[:255], "city": form["city"].strip(),
        "problem": form["problem"].strip()[:1000], "is_urgent": is_urgent,
        "total": estimate(offer["charge"], is_urgent)["total"],
    }, None


# Every slot for a date with a flag saying if it can still be booked.
def slot_choices(provider_id, booking_date):
    taken = booking_service.booked_slots(provider_id, booking_date)
    return [{"time": slot, "available": slot not in taken and not is_past_slot(booking_date, slot)}
            for slot in Config.TIME_SLOTS]


# JSON list of slots for a provider and date (used by main.js).
@booking_bp.route("/slots")
@login_required
def slots():
    booking_date = parse_date(request.args.get("date"))
    first, last = booking_date_range()
    if booking_date is None or not first <= booking_date <= last:
        return jsonify(slots=[], error="Invalid date"), 400
    return jsonify(slots=slot_choices(request.args.get("provider_id", type=int), booking_date))


# The customer's booking history with cancel and review buttons.
@booking_bp.route("/history")
@role_required("customer")
def history():
    return render_template("bookings/history.html",
                           bookings=booking_service.customer_bookings(g.user["id"]), today=date.today())


# Changes a booking's status (provider: accept/reject/start/complete, customer: cancel).
@booking_bp.route("/<int:booking_id>/status", methods=["POST"])
@role_required("customer", "provider")
def update_status(booking_id):
    booking = booking_service.get_booking(booking_id)
    if booking is None:
        abort(404)
    new_status = request.form.get("status", "")
    provider = get_provider_by_user(g.user["id"]) if g.user["role"] == "provider" else None
    if not booking_service.can_change(booking, g.user, provider and provider["id"], new_status):
        flash("That status change is not allowed.", "danger")
    else:
        reason = request.form.get("reason", "").strip()[:255] or None
        booking_service.change_status(booking, new_status, g.user["role"], reason)
        flash(f"Booking #{booking_id} marked as {new_status.replace('_', ' ')}.", "success")
    return redirect(request.referrer or url_for("main.index"))


# Review form for a completed booking that belongs to this customer.
@booking_bp.route("/<int:booking_id>/review", methods=["GET", "POST"])
@role_required("customer")
def review(booking_id):
    booking = booking_service.get_booking(booking_id)
    if booking is None or booking["customer_id"] != g.user["id"]:
        abort(404)
    if booking["status"] != "completed" or booking["review_id"]:
        flash("You can only review a completed booking once.", "warning")
        return redirect(url_for("booking.history"))
    if request.method == "POST" and save_review(booking, request.form):
        flash("Thanks for your review!", "success")
        return redirect(url_for("booking.history"))
    return render_template("bookings/review.html", booking=booking)


# Saves the review with its AI sentiment and refreshes the provider's rating.
def save_review(booking, form):
    rating = parse_rating(form.get("rating"))
    comment = form.get("comment", "").strip()[:1000]
    if rating is None:
        flash("Please choose a rating from 1 to 5.", "danger")
        return False
    result = sentiment_analyzer.predict(comment)
    sentiment, confidence = result if result else (None, None)
    try:
        execute("""INSERT INTO reviews (booking_id, customer_id, provider_id, rating, comment,
                   sentiment, sentiment_confidence) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (booking["id"], g.user["id"], booking["provider_id"], rating, comment or None,
                 sentiment, confidence), commit=False)
    except mysql.connector.IntegrityError:
        rollback()
        flash("This booking has already been reviewed.", "warning")
        return False
    refresh_provider_rating(booking["provider_id"])
    notify(booking["provider_user_id"], f"New {rating}★ review for booking #{booking['id']}.",
           url_for("provider.reviews"), commit=False)
    commit()
    return True


# Recalculates a provider's average rating and review count.
def refresh_provider_rating(provider_id):
    execute(
        """UPDATE providers SET
             avg_rating = (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE provider_id = %s),
             total_reviews = (SELECT COUNT(*) FROM reviews WHERE provider_id = %s)
           WHERE id = %s""",
        (provider_id, provider_id, provider_id), commit=False,
    )
