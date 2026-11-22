"""
app.py
Starting point of SmartHome AI.
Run with:  python3 app.py   then open http://127.0.0.1:5000
"""
from flask import Flask, jsonify, render_template, session, g, request
from flask_wtf.csrf import CSRFProtect, CSRFError

from config import Config
from utils.database import init_db, fetch_one
from utils.helpers import format_slot, format_inr
from services.admin_setup import ensure_admin_from_env
from services.notification_service import unread_count
from routes.main import main_bp
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.provider import provider_bp
from routes.admin import admin_bp
from routes.booking import booking_bp
from routes.ai import ai_bp

csrf = CSRFProtect()

ERROR_MESSAGES = {
    400: "The form expired or was invalid. Please go back and try again.",
    403: "You don't have permission to open this page.",
    404: "The page you are looking for doesn't exist.",
    500: "Something went wrong on our side. Please try again later.",
}


# Builds and configures the Flask app (the "app factory").
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing. Copy .env.example to .env and set it.")

    csrf.init_app(app)   # adds CSRF protection to every POST form
    init_db(app)         # sets up the MySQL connection pool
    register_blueprints(app)
    register_hooks(app)
    register_error_pages(app)
    app.jinja_env.filters["slot"] = format_slot
    app.jinja_env.filters["inr"] = format_inr
    ensure_admin_from_env(app)   # first admin from .env, if none exists yet
    return app


# Connects every route file (blueprint) to the app.
def register_blueprints(app):
    for blueprint in (main_bp, auth_bp, customer_bp, provider_bp, admin_bp, booking_bp, ai_bp):
        app.register_blueprint(blueprint)


# Loads the logged-in user before each request and shares data with templates.
def register_hooks(app):
    @app.before_request
    def load_logged_in_user():
        g.user = None if request.endpoint == "static" else load_user(session.get("user_id"))

    @app.context_processor
    def inject_navbar_data():
        user = g.get("user")
        return {"current_user": user, "unread_notifications": safe_unread_count(user)}

    @app.route("/health")
    def health():
        try:
            row = fetch_one("SELECT COUNT(*) AS total FROM services")
            return jsonify(status="ok", database="connected", services=row["total"])
        except Exception as error:
            return jsonify(status="error", database="unreachable", detail=str(error)), 500


# Returns the active user for this session; logs out deactivated users.
def load_user(user_id):
    if not user_id:
        return None
    user = fetch_one("SELECT id, name, email, role, city, is_active FROM users WHERE id = %s", (user_id,))
    if user is None or not user["is_active"]:
        session.clear()
        return None
    return user


# Unread notification count for the navbar badge (0 if it can't be read).
def safe_unread_count(user):
    try:
        return unread_count(user["id"]) if user else 0
    except Exception:
        return 0


# Shows the dark-themed error page for 400, 403, 404 and 500 errors.
def register_error_pages(app):
    def render_error(code):
        return render_template("errors/error.html", code=code, message=ERROR_MESSAGES[code]), code

    for code in (403, 404, 500):
        app.register_error_handler(code, lambda error, code=code: render_error(code))
    app.register_error_handler(CSRFError, lambda error: render_error(400))


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
