"""
ai_models/demand_forecast.py
AI feature 5: booking demand for the admin.
Weekday heatmap (counting) + next-week forecast (Linear Regression trend line).
"""
from datetime import date, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression

from utils.database import fetch_all

WEEKS = 8
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# Bookings per active service per weekday. MySQL WEEKDAY(): 0 = Monday.
def weekday_matrix():
    rows = fetch_all(
        """SELECT s.name, WEEKDAY(b.booking_date) AS weekday, COUNT(*) AS total
           FROM bookings b JOIN services s ON s.id = b.service_id
           WHERE s.is_active = 1 GROUP BY s.name, weekday"""
    )
    matrix = {}
    for row in rows:
        matrix.setdefault(row["name"], [0] * 7)[row["weekday"]] = row["total"]
    biggest = max((max(counts) for counts in matrix.values()), default=0)
    return {"rows": sorted(matrix.items()), "max": biggest}


# Bookings per service for each of the last WEEKS weeks, oldest week first.
def weekly_counts(today):
    rows = fetch_all(
        """SELECT service_id, DATEDIFF(%s, booking_date) DIV 7 AS weeks_ago, COUNT(*) AS total
           FROM bookings
           WHERE booking_date <= %s AND booking_date > %s
           GROUP BY service_id, weeks_ago""",
        (today, today, today - timedelta(days=WEEKS * 7)),
    )
    counts = {}
    for row in rows:
        counts.setdefault(row["service_id"], [0] * WEEKS)[WEEKS - 1 - row["weeks_ago"]] = row["total"]
    return counts


# Fits a straight trend line to weekly counts and predicts the next week.
# Returns (forecast, slope); forecast never goes below 0.
def forecast_next(counts):
    if sum(counts) == 0:
        return 0, 0.0
    weeks = np.arange(len(counts)).reshape(-1, 1)
    model = LinearRegression().fit(weeks, counts)
    prediction = model.predict([[len(counts)]])[0]
    return max(0, round(prediction)), round(float(model.coef_[0]), 2)


# Start date label for each of the last WEEKS weeks, e.g. "12 Oct".
def week_labels(today):
    return [(today - timedelta(days=7 * (WEEKS - 1 - i) + 6)).strftime("%d %b") for i in range(WEEKS)]


# Per-service table: last week, forecast for next week, and trend direction.
def service_forecasts(services, counts_by_service):
    table = []
    for service in services:
        counts = counts_by_service.get(service["id"], [0] * WEEKS)
        forecast, slope = forecast_next(counts)
        table.append({"name": service["name"], "icon": service["icon"], "last_week": counts[-1],
                      "total": sum(counts), "forecast": forecast, "slope": slope})
    return sorted(table, key=lambda row: row["forecast"], reverse=True)


# Everything the admin demand page needs, in one dict.
def demand_summary(services):
    today = date.today()
    counts_by_service = weekly_counts(today)
    overall = [sum(week) for week in zip(*counts_by_service.values())] or [0] * WEEKS
    forecast, slope = forecast_next(overall)
    return {
        "labels": week_labels(today), "overall": overall, "forecast": forecast, "slope": slope,
        "services": service_forecasts(services, counts_by_service),
        "heatmap": weekday_matrix(), "weekdays": WEEKDAYS,
    }
