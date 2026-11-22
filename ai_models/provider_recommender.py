"""
ai_models/provider_recommender.py
AI feature 2: ranks providers with a simple weighted formula (not ML).
score = rating 50% + experience 30% + price 20%  (weights from Config)
"""
from config import Config
from utils.database import fetch_all

CANDIDATE_SQL = """
    SELECT p.id, u.name, p.bio, p.experience_years, p.city,
           p.avg_rating, p.total_reviews, ps.charge
    FROM providers p
    JOIN users u ON u.id = p.user_id
    JOIN provider_services ps ON ps.provider_id = p.id
    WHERE ps.service_id = %s
      AND p.verification_status = 'verified'
      AND p.is_available = 1
      AND u.is_active = 1
      AND LOWER(p.city) = LOWER(%s)
"""


# Returns providers who can do this service in this city right now.
def get_candidates(service_id, city):
    return fetch_all(CANDIDATE_SQL, (service_id, city.strip()))


# Calculates a 0-100 score from rating, experience and price.
def score_provider(provider, lowest_charge, weights):
    rating_part = float(provider["avg_rating"]) / 5
    experience_part = min(provider["experience_years"], 10) / 10
    price_part = float(lowest_charge) / float(provider["charge"])
    total = (weights["rating"] * rating_part
             + weights["experience"] * experience_part
             + weights["price"] * price_part)
    return round(total * 100, 1)


# Builds 1-2 plain-language reasons for showing this provider.
def build_reasons(provider, lowest_charge):
    reasons = []
    if float(provider["avg_rating"]) >= 4:
        reasons.append(f"Highly rated ({float(provider['avg_rating']):.1f}★)")
    if provider["experience_years"] >= 5:
        reasons.append(f"{provider['experience_years']} years experience")
    if float(provider["charge"]) == float(lowest_charge):
        reasons.append("Lowest price")
    if not reasons:
        reasons.append("New on SmartHome" if provider["total_reviews"] == 0
                       else f"{provider['experience_years']} years experience")
    return reasons[:2]


# Returns candidates sorted best first, each with "score" and "reasons" added.
def rank_providers(service_id, city):
    providers = get_candidates(service_id, city) if city else []
    if not providers:
        return []
    lowest = min(float(p["charge"]) for p in providers)
    for provider in providers:
        provider["score"] = score_provider(provider, lowest, Config.RANK_WEIGHTS)
        provider["reasons"] = build_reasons(provider, lowest)
    return sorted(providers, key=lambda p: p["score"], reverse=True)
