"""
ai_models/sentiment_analyzer.py
AI feature 3: labels a review as positive, negative or neutral.
"""
from ai_models.model_loader import load_model, predict_label

MODEL_FILE = "sentiment_model.joblib"


# True if the trained model file exists.
def is_ready():
    return load_model(MODEL_FILE) is not None


# Returns (sentiment, confidence %) or None if the model is missing or text is empty.
def predict(text):
    if not (text or "").strip():
        return None
    return predict_label(MODEL_FILE, text)
