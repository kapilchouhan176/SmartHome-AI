"""
seed_data.py
Adds demo customers, providers, bookings and reviews for testing.
Safe to run again: it first deletes the old demo accounts (@demo.com).
Indore data lives in seed_indore.py. Run with:  python3 seed_data.py
"""
import random
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

import seed_indore as indore
from ai_models import sentiment_analyzer, service_classifier
from app import create_app
from config import Config
from services.notification_service import notify
from utils.database import execute, fetch_one, commit

DEMO_PASSWORD = "demo1234"

# name, email, phone, city, address
CUSTOMERS = [
    ("Aarav Sharma", "aarav@demo.com", "9876500001", "Mumbai", "12 Marine Drive, Mumbai"),
    ("Priya Nair", "priya@demo.com", "9876500002", "Mumbai", "45 Bandra West, Mumbai"),
    ("Rohan Verma", "rohan@demo.com", "9876500003", "Pune", "8 Koregaon Park, Pune"),
    ("Neha Gupta", "neha@demo.com", "9876500004", "Mumbai", "3 Powai, Mumbai"),
    ("Karan Mehta", "karan@demo.com", "9876500005", "Mumbai", "21 Andheri East, Mumbai"),
    ("Sneha Iyer", "sneha@demo.com", "9876500006", "Mumbai", "9 Chembur, Mumbai"),
    ("Vikram Singh", "vikram@demo.com", "9876500007", "Mumbai", "14 Dadar, Mumbai"),
    ("Ananya Rao", "ananya@demo.com", "9876500008", "Pune", "5 Baner, Pune"),
    ("Arjun Patil", "arjun@demo.com", "9876500009", "Pune", "17 Kothrud, Pune"),
]

HISTORY_SIZE = 70           # random past bookings in Mumbai/Pune
INDORE_HISTORY = 400        # random past bookings in Indore
INDORE_UPCOMING = 40        # pending/accepted/in-progress Indore bookings

# name, email, phone, city, experience, bio, status, {service: charge}
PROVIDERS = [
    ("Ramesh Plumbing Works", "ramesh@demo.com", "9876511001", "Mumbai", 12, "Expert plumber, 24x7 leak repairs.",
     "verified", {"Plumbing": 349, "Carpentry": 399}),
    ("Suresh Kumar", "suresh@demo.com", "9876511002", "Mumbai", 4, "Quick and affordable plumbing fixes.",
     "verified", {"Plumbing": 279}),
    ("Volt Electricals", "volt@demo.com", "9876511003", "Mumbai", 8, "Licensed electricians for homes and offices.",
     "verified", {"Electrical Repair": 299, "Appliance Repair": 399}),
    ("CoolAir Services", "coolair@demo.com", "9876511004", "Mumbai", 6, "AC servicing, gas refill and installation.",
     "verified", {"AC Repair and Maintenance": 549, "Appliance Repair": 379}),
    ("Sparkle Cleaners", "sparkle@demo.com", "9876511005", "Mumbai", 3, "Deep cleaning with eco-friendly products.",
     "verified", {"Home Cleaning": 899}),
    ("BugFree Pest Control", "bugfree@demo.com", "9876511006", "Mumbai", 10, "Safe, odourless pest treatments.",
     "verified", {"Pest Control": 749}),
    ("ColorCraft Painters", "colorcraft@demo.com", "9876511007", "Pune", 9, "Interior and exterior painting experts.",
     "verified", {"Painting": 1599}),
    ("Pune Home Fixers", "punefix@demo.com", "9876511008", "Pune", 5, "Plumbing and electrical in one visit.",
     "verified", {"Plumbing": 299, "Electrical Repair": 269}),
    ("New Pro Pending", "pending@demo.com", "9876511009", "Mumbai", 2, "Just joined, awaiting verification.",
     "pending", {"Plumbing": 249}),
]

# customer email, provider email, service, days from today, slot, status, (rating, comment) or None
BOOKINGS = [
    ("aarav@demo.com", "ramesh@demo.com", "Plumbing", -10, "11:00", "completed",
     (5, "Excellent service. Fixed the leak quickly and cleaned up after the work.")),
    ("priya@demo.com", "ramesh@demo.com", "Plumbing", -6, "09:00", "completed",
     (4, "Very good work, came on time and was polite.")),
    ("aarav@demo.com", "volt@demo.com", "Electrical Repair", -8, "15:00", "completed",
     (3, "Service was okay. Took longer than expected.")),
    ("priya@demo.com", "coolair@demo.com", "AC Repair and Maintenance", -5, "13:00", "completed",
     (2, "Not happy. The technician came late and AC is still not cooling well.")),
    ("aarav@demo.com", "sparkle@demo.com", "Home Cleaning", -3, "09:00", "completed", None),
    ("rohan@demo.com", "colorcraft@demo.com", "Painting", -4, "11:00", "completed",
     (5, "Superb painting job, very neat. Highly recommended.")),
    ("aarav@demo.com", "ramesh@demo.com", "Plumbing", 2, "11:00", "pending", None),
    ("priya@demo.com", "volt@demo.com", "Electrical Repair", 3, "15:00", "accepted", None),
    ("aarav@demo.com", "bugfree@demo.com", "Pest Control", 1, "17:00", "in_progress", None),
    ("priya@demo.com", "suresh@demo.com", "Plumbing", -2, "13:00", "cancelled", None),
    ("rohan@demo.com", "punefix@demo.com", "Electrical Repair", -1, "09:00", "rejected", None),
]


# Deletes earlier demo accounts and their AI logs; other rows go via ON DELETE CASCADE.
def clear_demo_data():
    execute("DELETE FROM ai_predictions WHERE user_id IN (SELECT id FROM users WHERE email LIKE %s)", ("%@demo.com",))
    execute("DELETE FROM users WHERE email LIKE %s", ("%@demo.com",))


# Inserts one user and returns the new id.
def add_user(name, email, phone, role, city, address=None):
    return execute(
        """INSERT INTO users (name, email, password_hash, phone, role, city, address)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (name, email, PASSWORD_HASH, phone, role, city, address), commit=False)


# Inserts a provider with their services; returns the providers.id.
def add_provider(name, email, phone, city, experience, bio, status, services):
    user_id = add_user(name, email, phone, "provider", city)
    provider_id = execute(
        """INSERT INTO providers (user_id, bio, experience_years, city, verification_status)
           VALUES (%s, %s, %s, %s, %s)""", (user_id, bio, experience, city, status), commit=False)
    for service_name, charge in services.items():
        execute("INSERT INTO provider_services (provider_id, service_id, charge) VALUES (%s, %s, %s)",
                (provider_id, service_id(service_name), charge), commit=False)
    return provider_id


# Looks up a service id by its name.
def service_id(name):
    return fetch_one("SELECT id FROM services WHERE name = %s", (name,))["id"]


# Inserts one booking (and its review, if given). Returns the booking id.
def add_booking(customer, provider_id, service_name, days, slot, status, review, problem=None, urgent=False):
    customer_id, city, address = customer
    charge = float(fetch_one("SELECT charge FROM provider_services WHERE provider_id = %s AND service_id = %s",
                             (provider_id, service_id(service_name)))["charge"])
    cost = charge + (Config.URGENT_CHARGE if urgent else 0)
    booking_id = execute(
        """INSERT INTO bookings (customer_id, provider_id, service_id, booking_date, time_slot, address,
               city, problem_description, is_urgent, estimated_cost, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (customer_id, provider_id, service_id(service_name), date.today() + timedelta(days=days), slot,
         address or "Demo address", city, problem or f"Demo request for {service_name.lower()}.",
         urgent, cost, status), commit=False)
    if review:
        add_review(booking_id, customer_id, provider_id, *review)
    return booking_id


# Inserts a review with its predicted sentiment.
def add_review(booking_id, customer_id, provider_id, rating, comment):
    sentiment, confidence = sentiment_analyzer.predict(comment) or (None, None)
    execute("""INSERT INTO reviews (booking_id, customer_id, provider_id, rating, comment, sentiment,
               sentiment_confidence) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (booking_id, customer_id, provider_id, rating, comment, sentiment, confidence), commit=False)


# Random past bookings in Mumbai/Pune (more in recent weeks), fixed seed.
def add_history(customers, providers):
    rng = random.Random(7)
    verified = [p for p in PROVIDERS if p[6] == "verified"]
    mumbai_pune = [email for email, c in customers.items() if c[1] in ("Mumbai", "Pune")]
    for _ in range(HISTORY_SIZE):
        email = rng.choice(mumbai_pune)
        provider = rng.choice([p for p in verified if p[3] == customers[email][1]])
        status = rng.choices(["completed", "cancelled"], weights=[85, 15])[0]
        add_booking(customers[email], providers[provider[1]], rng.choice(list(provider[7])),
                    -round(rng.triangular(1, 56, 1)), rng.choice(Config.TIME_SLOTS), status, None)


# Adds the Indore customers and providers from seed_indore.py.
def add_indore_people(customers, providers):
    for name, email, phone, locality in indore.CUSTOMERS:
        address = f"{indore.LOCALITIES.index(locality) + 10} {locality}, Indore"
        customers[email] = (add_user(name, email, phone, "customer", "Indore", address), "Indore", address)
    for name, email, phone, exp, bio, status, services, _quality in indore.PROVIDERS:
        providers[email] = add_provider(name, email, phone, "Indore", exp, bio, status, services)
    for email in indore.UNAVAILABLE:
        execute("UPDATE providers SET is_available = 0 WHERE id = %s", (providers[email],), commit=False)


# Picks a star rating near the provider's typical quality, from 1 to 5.
def pick_rating(rng, quality):
    return max(1, min(5, round(rng.gauss(quality, 0.6))))


# Past Indore bookings: mostly completed, ~70% of those reviewed.
def add_indore_history(rng, customers, providers):
    verified = [p for p in indore.PROVIDERS if p[5] == "verified"]
    indore_customers = [c[1] for c in indore.CUSTOMERS]
    for _ in range(INDORE_HISTORY):
        name, email, _p, _e, _b, _s, services, quality = rng.choice(verified)
        service = rng.choice(list(services))
        status = rng.choices(["completed", "cancelled", "rejected"], weights=[78, 12, 10])[0]
        review = None
        if status == "completed" and rng.random() < 0.7:
            rating = pick_rating(rng, quality)
            review = (rating, rng.choice(indore.REVIEWS[rating]))
        add_booking(customers[rng.choice(indore_customers)], providers[email], service,
                    -round(rng.triangular(1, 56, 1)), rng.choice(Config.TIME_SLOTS), status, review,
                    rng.choice(indore.PROBLEMS[service]), urgent=rng.random() < 0.15)


# Upcoming Indore bookings for providers to act on; skips taken slots.
def add_indore_upcoming(rng, customers, providers):
    bookable = [p for p in indore.PROVIDERS if p[5] == "verified" and p[1] not in indore.UNAVAILABLE]
    indore_customers = [c[1] for c in indore.CUSTOMERS]
    taken = set()
    for _ in range(INDORE_UPCOMING):
        name, email, *_rest = provider = rng.choice(bookable)
        service = rng.choice(list(provider[6]))
        status = rng.choices(["pending", "accepted", "in_progress"], weights=[50, 35, 15])[0]
        days = 0 if status == "in_progress" else rng.randint(1, 10)
        slot = "17:00" if days == 0 else rng.choice(Config.TIME_SLOTS)
        if (email, days, slot) in taken:
            continue
        taken.add((email, days, slot))
        add_booking(customers[rng.choice(indore_customers)], providers[email], service, days, slot, status,
                    None, rng.choice(indore.PROBLEMS[service]), urgent=rng.random() < 0.2)
        if status == "pending":
            notify_provider(providers[email], service)


# Sends the provider a "new booking request" notification.
def notify_provider(provider_id, service):
    user = fetch_one("SELECT user_id FROM providers WHERE id = %s", (provider_id,))
    notify(user["user_id"], f"New booking request for {service}.", "/provider/dashboard", commit=False)


# Logs sample AI suggestions from Indore customers over the last 30 days.
def add_ai_predictions(rng, customers):
    if not service_classifier.is_ready():
        return
    for text in indore.AI_QUERIES * 2:
        name, confidence = service_classifier.predict(text)
        service = fetch_one("SELECT id FROM services WHERE name = %s", (name,))
        when = datetime.now() - timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 23))
        execute("""INSERT INTO ai_predictions (user_id, input_text, predicted_service_id, confidence, created_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (customers[rng.choice(indore.CUSTOMERS)[1]][0], text, service["id"] if service else None,
                 confidence, when), commit=False)


# Recalculates avg_rating and total_reviews for every provider.
def refresh_ratings():
    execute("""UPDATE providers p SET
                 avg_rating = (SELECT COALESCE(AVG(rating), 0) FROM reviews r WHERE r.provider_id = p.id),
                 total_reviews = (SELECT COUNT(*) FROM reviews r WHERE r.provider_id = p.id)""", commit=False)


# Runs all the steps above inside one transaction.
def main():
    if not sentiment_analyzer.is_ready():
        print("Note: sentiment model not found, reviews will be saved without sentiment.")
    clear_demo_data()
    customers = {c[1]: (add_user(c[0], c[1], c[2], "customer", c[3], c[4]), c[3], c[4]) for c in CUSTOMERS}
    providers = {p[1]: add_provider(*p) for p in PROVIDERS}
    for cust, prov, service, days, slot, status, review in BOOKINGS:
        add_booking(customers[cust], providers[prov], service, days, slot, status, review)
    add_history(customers, providers)
    rng = random.Random(42)
    add_indore_people(customers, providers)
    add_indore_history(rng, customers, providers)
    add_indore_upcoming(rng, customers, providers)
    add_ai_predictions(rng, customers)
    refresh_ratings()
    commit()
    print_summary()


# Prints how many demo rows now exist.
def print_summary():
    row = fetch_one(
        """SELECT (SELECT COUNT(*) FROM users WHERE email LIKE '%demo.com' AND role = 'customer') AS customers,
                  (SELECT COUNT(*) FROM users WHERE email LIKE '%demo.com' AND role = 'provider') AS providers,
                  (SELECT COUNT(*) FROM bookings) AS bookings, (SELECT COUNT(*) FROM reviews) AS reviews""")
    print(f"Seeded {row['customers']} customers, {row['providers']} providers, "
          f"{row['bookings']} bookings, {row['reviews']} reviews.")
    print(f"All demo accounts use the password: {DEMO_PASSWORD}")


PASSWORD_HASH = generate_password_hash(DEMO_PASSWORD)   # hashed once; hashing is slow

if __name__ == "__main__":
    with create_app().app_context():
        main()
