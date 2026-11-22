"""
services/dashboard_service.py
Extra content for the customer dashboard: popular services,
top-rated providers and recommendations, all for the customer's city.
"""
from ai_models.related_services import related_services
from utils.database import fetch_all


# Active services ordered by how often they were booked in this city.
def popular_services(city, limit=8):
    return fetch_all(
        """SELECT s.id, s.name, s.icon, s.base_price, COUNT(b.id) AS bookings
           FROM services s
           LEFT JOIN bookings b ON b.service_id = s.id AND LOWER(b.city) = LOWER(%s)
           WHERE s.is_active = 1
           GROUP BY s.id, s.name, s.icon, s.base_price
           ORDER BY bookings DESC, s.name LIMIT %s""",
        (city or "", limit),
    )


# Best-rated bookable providers in this city, with the services they offer.
def top_providers(city, limit=4):
    if not city:
        return []
    return fetch_all(
        """SELECT p.id, u.name, p.avg_rating, p.total_reviews, p.experience_years,
                  MIN(ps.charge) AS min_charge, MIN(s.id) AS service_id,
                  GROUP_CONCAT(s.name ORDER BY s.name SEPARATOR ', ') AS services
           FROM providers p
           JOIN users u ON u.id = p.user_id
           JOIN provider_services ps ON ps.provider_id = p.id
           JOIN services s ON s.id = ps.service_id AND s.is_active = 1
           WHERE p.verification_status = 'verified' AND p.is_available = 1
             AND u.is_active = 1 AND LOWER(p.city) = LOWER(%s)
           GROUP BY p.id, u.name, p.avg_rating, p.total_reviews, p.experience_years
           ORDER BY p.avg_rating DESC, p.total_reviews DESC, p.experience_years DESC
           LIMIT %s""",
        (city, limit),
    )


# "Customers also booked" for the customer's most recent booking (or None).
def recommendations(bookings):
    if not bookings:
        return None
    latest = max(bookings, key=lambda b: b["created_at"])
    items = related_services(latest["service_id"])
    return {"based_on": latest["service_name"], "items": items} if items else None
