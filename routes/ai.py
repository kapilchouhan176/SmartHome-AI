"""
routes/ai.py
AI service suggestion page: the customer describes a problem
and the ML model suggests a service category.
"""
from flask import Blueprint, render_template, request, flash, g

from ai_models import service_classifier
from config import Config
from utils.database import fetch_one, execute
from utils.helpers import get_active_services

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


# Shows the problem box; on POST predicts the service and logs it.
@ai_bp.route("/suggest", methods=["GET", "POST"])
def suggest():
    text = request.form.get("problem", "").strip()
    result = None
    if request.method == "POST":
        if len(text) < 5:
            flash("Please describe the problem in a few words.", "warning")
        else:
            result = run_prediction(text[:1000])
    return render_template("customer/suggest.html", text=text, result=result,
                           model_ready=service_classifier.is_ready(),
                           services=get_active_services())


# Predicts, finds the matching service row and logs the prediction.
# Returns a dict for the template, or None if the model is missing.
def run_prediction(text):
    prediction = service_classifier.predict(text)
    if prediction is None:
        return None
    name, confidence = prediction
    service = fetch_one("SELECT * FROM services WHERE name = %s AND is_active = 1", (name,))
    log_prediction(text, service, confidence)
    confident = service is not None and confidence >= Config.LOW_CONFIDENCE
    return {"service": service, "name": name, "confidence": confidence, "confident": confident}


# Saves the prediction to ai_predictions for the admin stats.
def log_prediction(text, service, confidence):
    user_id = g.user["id"] if g.get("user") else None
    execute(
        "INSERT INTO ai_predictions (user_id, input_text, predicted_service_id, confidence) VALUES (%s, %s, %s, %s)",
        (user_id, text, service["id"] if service else None, confidence),
    )
