"""
train_models.py
Trains both ML models, prints their evaluation and saves them.
Run with:  python3 train_models.py
"""
import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config import Config, BASE_DIR

DATASET_DIR = os.path.join(BASE_DIR, "datasets")


# TF-IDF + Logistic Regression. C=10 (weaker regularisation) gives useful confidence scores
# on our small dataset; stop_words=None keeps "not", so "not good" stays negative.
def build_pipeline(stop_words):
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, stop_words=stop_words)),
        ("clf", LogisticRegression(max_iter=1000, C=10)),
    ])


# Trains on 80% of the CSV, tests on 20%, prints results and saves the model.
def train_and_evaluate(title, csv_name, label_column, model_name, stop_words):
    data = pd.read_csv(os.path.join(DATASET_DIR, csv_name))
    x_train, x_test, y_train, y_test = train_test_split(
        data["text"], data[label_column], test_size=0.2, stratify=data[label_column], random_state=42)
    model = build_pipeline(stop_words).fit(x_train, y_train)
    print_report(title, len(data), y_test, model.predict(x_test))
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(Config.MODEL_DIR, model_name))
    print(f"Saved -> ai_models/saved_models/{model_name}\n")


# Prints accuracy and precision/recall/F1 for each class.
def print_report(title, total_rows, y_true, y_pred):
    print("=" * 60)
    print(f"{title}  ({total_rows} rows, {len(y_true)} used for testing)")
    print("=" * 60)
    print(f"Accuracy: {accuracy_score(y_true, y_pred) * 100:.2f}%\n")
    print(classification_report(y_true, y_pred, zero_division=0))


# Trains the service classifier and the sentiment model.
def main():
    train_and_evaluate("1. Service suggestion model", "service_queries.csv", "service",
                       "service_model.joblib", stop_words="english")
    train_and_evaluate("2. Review sentiment model", "reviews.csv", "sentiment",
                       "sentiment_model.joblib", stop_words=None)
    print("Done. Restart the Flask app so it loads the new models.")


if __name__ == "__main__":
    main()
