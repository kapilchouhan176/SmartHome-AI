"""
services/admin_setup.py
Creates admin accounts. Admins never sign up on the website: they come from
ADMIN_* values in .env (on app start) or from `python3 create_admin.py`.
"""
import mysql.connector
from werkzeug.security import generate_password_hash

from utils.database import fetch_one, execute
from utils.validators import is_valid_email, is_valid_password


# Returns an error message if the admin details are invalid, else None.
def validate_admin(name, email, password):
    if not name:
        return "Admin name is required."
    if not is_valid_email(email):
        return "Admin email is not a valid email address."
    if not is_valid_password(password):
        return "Admin password must be at least 8 characters."
    return None


# Inserts an admin user. Returns (True, message) or (False, error).
def create_admin(name, email, password):
    email = (email or "").strip().lower()
    error = validate_admin((name or "").strip(), email, password)
    if error:
        return False, error
    if fetch_one("SELECT id FROM users WHERE email = %s", (email,)):
        return False, f"A user with email {email} already exists."
    execute("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
            (name.strip(), email, generate_password_hash(password)))
    return True, f"Admin {email} created."


# True if at least one admin account exists.
def admin_exists():
    return fetch_one("SELECT id FROM users WHERE role = 'admin' LIMIT 1") is not None


# On app start: creates the first admin from .env if no admin exists yet.
# Never stops the app; problems are only written to the log.
def ensure_admin_from_env(app):
    config = app.config
    if not (config["ADMIN_EMAIL"] and config["ADMIN_PASSWORD"]):
        return
    with app.app_context():
        try:
            if not admin_exists():
                ok, message = create_admin(config["ADMIN_NAME"], config["ADMIN_EMAIL"], config["ADMIN_PASSWORD"])
                (app.logger.info if ok else app.logger.warning)(f"Admin setup: {message}")
        except mysql.connector.Error as error:
            app.logger.warning(f"Admin setup skipped, database not ready: {error}")
