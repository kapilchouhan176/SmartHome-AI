"""
config.py
Central settings for SmartHome AI.
Secret values are read from the .env file, never written in code.
"""
import os
from dotenv import load_dotenv

# Load variables from the .env file in the project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # --- Security ---
    SECRET_KEY = os.getenv("SECRET_KEY")
    WTF_CSRF_TIME_LIMIT = None           # CSRF token valid for the whole session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"   # set 1 when served over HTTPS
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"                              # never 1 on a live server

    # --- First admin, created automatically on start if no admin exists ---
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrator")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # --- Database ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "home_service_db")
    DB_SSL_CA = os.getenv("DB_SSL_CA", "")   # path to the CA certificate of a cloud MySQL; empty locally

    # --- Booking ---
    # Fixed 2-hour time slots a customer can choose from
    TIME_SLOTS = ["09:00", "11:00", "13:00", "15:00", "17:00"]
    URGENT_CHARGE = 150                   # extra ₹ for same-day urgent service
    BOOKING_DAYS_AHEAD = 30               # customers can book up to 30 days ahead

    # --- Provider ranking weights (must add up to 1.0) ---
    RANK_WEIGHTS = {
        "rating": 0.5,
        "experience": 0.3,
        "price": 0.2,
    }

    # --- AI model files ---
    MODEL_DIR = os.path.join(BASE_DIR, "ai_models", "saved_models")
    LOW_CONFIDENCE = 40                   # below this %, ask the user to pick a service
