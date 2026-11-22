"""
ai_models/model_loader.py
Loads saved scikit-learn models from disk (once) and makes predictions.
Shared by the service classifier and the sentiment analyzer.
"""
import os

import joblib

from config import Config

_cache = {}


# Loads a model file from MODEL_DIR. Returns None if it has not been trained yet.
def load_model(filename):
    if filename not in _cache:
        path = os.path.join(Config.MODEL_DIR, filename)
        if not os.path.exists(path):
            return None
        _cache[filename] = joblib.load(path)
    return _cache[filename]


# Predicts a label for the text. Returns (label, confidence %) or None.
def predict_label(filename, text):
    model = load_model(filename)
    if model is None:
        return None
    probabilities = model.predict_proba([text])[0]
    best = probabilities.argmax()
    return str(model.classes_[best]), round(float(probabilities[best]) * 100, 2)
