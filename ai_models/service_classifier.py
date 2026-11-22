"""
ai_models/service_classifier.py
AI feature 1: suggests a service category from the customer's problem text.
"""
from ai_models.model_loader import load_model, predict_label

MODEL_FILE = "service_model.joblib"


# True if the trained model file exists.
def is_ready():
    return load_model(MODEL_FILE) is not None


# Returns (service_name, confidence %) or None if the model is missing.
def predict(text):
    return predict_label(MODEL_FILE, text)
