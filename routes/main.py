"""
routes/main.py
Public pages: home, service listing, service details, and notifications.
"""
from flask import Blueprint, render_template, request, g, abort

from ai_models.provider_recommender import rank_providers
from ai_models.related_services import related_services
from services.notification_service import get_notifications, mark_all_read
from utils.database import fetch_all
from utils.decorators import login_required
from utils.helpers import get_active_services, get_active_service

main_bp = Blueprint("main", __name__)


# Home page with the service categories and an AI suggestion box.
@main_bp.route("/")
def index():
    return render_template("index.html", services=get_active_services())


# Lists active services; `q` searches the name and description.
@main_bp.route("/services")
def services():
    query = request.args.get("q", "").strip()
    if query:
        like = f"%{query}%"
        rows = fetch_all(
            """SELECT * FROM services WHERE is_active = 1
               AND (name LIKE %s OR description LIKE %s) ORDER BY name""",
            (like, like),
        )
    else:
        rows = get_active_services()
    return render_template("services.html", services=rows, query=query)


# Shows one service and the ranked providers in the chosen city.
@main_bp.route("/services/<int:service_id>")
def service_detail(service_id):
    service = get_active_service(service_id)
    if service is None:
        abort(404)
    city = request.args.get("city", "").strip() or default_city()
    providers = rank_providers(service_id, city)
    return render_template("service_detail.html", service=service, city=city, providers=providers,
                           related=related_services(service_id))


# The logged-in user's city, used to pre-fill the provider search.
def default_city():
    user = g.get("user")
    return (user["city"] or "") if user else ""


# Lists the user's notifications and marks them as read.
@main_bp.route("/notifications")
@login_required
def notifications():
    items = get_notifications(g.user["id"])
    mark_all_read(g.user["id"])
    return render_template("notifications.html", notifications=items)
