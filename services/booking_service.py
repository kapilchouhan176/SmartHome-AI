"""
services/booking_service.py
Booking rules: who can book whom, which slots are free,
and which status changes are allowed.
"""
from flask import url_for

from utils.database import fetch_one, fetch_all, execute, commit
from utils.helpers import format_slot
from services.notification_service import notify

# Allowed status changes for each role: current status -> new statuses
PROVIDER_MOVES = {
    "pending": ("accepted", "rejected"),
    "accepted": ("in_progress",),
    "in_progress": ("completed",),
}
CUSTOMER_MOVES = {
    "pending": ("cancelled",),
    "accepted": ("cancelled",),
}

# One SELECT with all names a booking page needs
BOOKING_SELECT = """
    SELECT b.*, s.name AS service_name, s.icon AS service_icon,
           cu.name AS customer_name, cu.phone AS customer_phone,
           pu.name AS provider_name, pu.phone AS provider_phone,
           p.user_id AS provider_user_id,
           r.id AS review_id
    FROM bookings b
    JOIN services s   ON s.id = b.service_id
    JOIN users cu     ON cu.id = b.customer_id
    JOIN providers p  ON p.id = b.provider_id
    JOIN users pu     ON pu.id = p.user_id
    LEFT JOIN reviews r ON r.booking_id = b.id
"""


# Returns a provider's offer for a service if the provider can be booked.
# Bookable = verified, available, active account, active service.
def get_offer(provider_id, service_id):
    return fetch_one(
        """SELECT p.id AS provider_id, p.city, p.experience_years, p.avg_rating,
                  p.total_reviews, u.name AS provider_name,
                  s.id AS service_id, s.name AS service_name, s.icon, ps.charge
           FROM provider_services ps
           JOIN providers p ON p.id = ps.provider_id
           JOIN users u     ON u.id = p.user_id
           JOIN services s  ON s.id = ps.service_id
           WHERE ps.provider_id = %s AND ps.service_id = %s
             AND p.verification_status = 'verified' AND p.is_available = 1
             AND u.is_active = 1 AND s.is_active = 1""",
        (provider_id, service_id),
    )


# Returns the set of slots ("HH:MM") already taken for a provider on a date.
def booked_slots(provider_id, booking_date):
    rows = fetch_all(
        """SELECT time_slot FROM bookings
           WHERE provider_id = %s AND booking_date = %s AND active_slot = 1""",
        (provider_id, booking_date),
    )
    return {format_slot(row["time_slot"]) for row in rows}


# Inserts a new booking and notifies the provider in one transaction.
# Raises mysql IntegrityError (1062) if the slot was taken a moment ago.
def create_booking(data, offer):
    booking_id = execute(
        """INSERT INTO bookings (customer_id, provider_id, service_id, booking_date,
                time_slot, address, city, problem_description, is_urgent, estimated_cost)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (data["customer_id"], offer["provider_id"], offer["service_id"], data["booking_date"],
         data["slot"], data["address"], data["city"], data["problem"], data["is_urgent"],
         data["total"]),
        commit=False,
    )
    provider_user = fetch_one("SELECT user_id FROM providers WHERE id = %s", (offer["provider_id"],))
    notify(provider_user["user_id"],
           f"New booking request for {offer['service_name']} on {data['booking_date']} at {data['slot']}.",
           url_for("provider.dashboard"), commit=False)
    commit()
    return booking_id


# Returns one booking with service, customer and provider names.
def get_booking(booking_id):
    return fetch_one(BOOKING_SELECT + " WHERE b.id = %s", (booking_id,))


# Returns all bookings made by a customer, newest first.
def customer_bookings(customer_id):
    return fetch_all(BOOKING_SELECT + " WHERE b.customer_id = %s ORDER BY b.booking_date DESC, b.time_slot DESC",
                     (customer_id,))


# Returns all bookings received by a provider, newest first.
def provider_bookings(provider_id):
    return fetch_all(BOOKING_SELECT + " WHERE b.provider_id = %s ORDER BY b.booking_date DESC, b.time_slot DESC",
                     (provider_id,))


# True if the user (by role and ownership) may move the booking to new_status.
def can_change(booking, user, provider_id, new_status):
    if user["role"] == "customer" and booking["customer_id"] == user["id"]:
        return new_status in CUSTOMER_MOVES.get(booking["status"], ())
    if user["role"] == "provider" and booking["provider_id"] == provider_id:
        return new_status in PROVIDER_MOVES.get(booking["status"], ())
    return False


# Saves the new status and notifies the other party of the booking.
def change_status(booking, new_status, actor_role, reason=None):
    execute("UPDATE bookings SET status = %s, cancel_reason = %s WHERE id = %s",
            (new_status, reason, booking["id"]), commit=False)
    notify_other_party(booking, new_status, actor_role)
    commit()


# Sends a notification to whoever did NOT make the change.
def notify_other_party(booking, new_status, actor_role):
    label = new_status.replace("_", " ")
    message = f"Booking #{booking['id']} ({booking['service_name']}) is now {label}."
    if actor_role == "provider":
        notify(booking["customer_id"], message, url_for("booking.history"), commit=False)
    else:
        notify(booking["provider_user_id"], message, url_for("provider.dashboard"), commit=False)
