"""
ai_models/related_services.py
AI feature 4: "Customers also booked" — a simple co-occurrence count
over booking history (no model training needed).
"""
from utils.database import fetch_all

# Counts other services booked by customers who booked this one.
# Rejected and cancelled bookings are ignored.
RELATED_SQL = """
    SELECT s.id, s.name, s.icon, s.base_price,
           COUNT(DISTINCT b2.customer_id) AS customers
    FROM bookings b1
    JOIN bookings b2 ON b2.customer_id = b1.customer_id AND b2.service_id <> b1.service_id
    JOIN services s  ON s.id = b2.service_id
    WHERE b1.service_id = %s
      AND s.is_active = 1
      AND b1.status NOT IN ('rejected', 'cancelled')
      AND b2.status NOT IN ('rejected', 'cancelled')
    GROUP BY s.id, s.name, s.icon, s.base_price
    ORDER BY customers DESC, s.name
    LIMIT %s
"""


# Returns up to `limit` services most often booked by the same customers.
def related_services(service_id, limit=3):
    return fetch_all(RELATED_SQL, (service_id, limit))
