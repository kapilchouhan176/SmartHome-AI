"""
utils/validators.py
Server-side form checks. Browser checks can be skipped by users,
so every form is validated again here.
"""
import re
from datetime import date, datetime

from config import Config
from utils.helpers import booking_date_range

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_CHARGE = 1_000_000


# True if the text looks like an email address.
def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))


# True if the phone number is exactly 10 digits.
def is_valid_phone(phone):
    return bool(re.fullmatch(r"\d{10}", phone or ""))


# True if the password has at least 8 characters.
def is_valid_password(password):
    return len(password or "") >= 8


# Returns an error message for every required field that is empty.
# `fields` maps form field name -> label shown to the user.
def missing_fields(form, fields):
    return [f"{label} is required." for name, label in fields.items()
            if not (form.get(name) or "").strip()]


# Converts a rating to an int from 1 to 5, or None if invalid.
def parse_rating(value):
    number = _to_number(value, int)
    return number if number is not None and 1 <= number <= 5 else None


# Converts a price to a positive float, or None if invalid.
def parse_charge(value):
    number = _to_number(value, float)
    return round(number, 2) if number is not None and 0 < number <= MAX_CHARGE else None


# Converts years of experience to an int from 0 to 60, or None if invalid.
def parse_experience(value):
    number = _to_number(value, int)
    return number if number is not None and 0 <= number <= 60 else None


# Checks the booking date and slot. Returns (date, None) or (None, error).
def validate_date_and_slot(date_text, slot):
    booking_date = parse_date(date_text)
    first, last = booking_date_range()
    if booking_date is None:
        return None, "Please choose a valid date."
    if not first <= booking_date <= last:
        return None, f"Date must be between today and {Config.BOOKING_DAYS_AHEAD} days ahead."
    if slot not in Config.TIME_SLOTS:
        return None, "Please choose a valid time slot."
    if is_past_slot(booking_date, slot):
        return None, "That time slot has already passed. Please pick a later one."
    return booking_date, None


# True if the slot is today and its start time has already gone by.
def is_past_slot(booking_date, slot):
    slot_time = datetime.strptime(slot, "%H:%M").time()
    return booking_date == date.today() and slot_time <= datetime.now().time()


# Converts "YYYY-MM-DD" text into a date, or None if invalid.
def parse_date(text):
    try:
        return datetime.strptime(text or "", "%Y-%m-%d").date()
    except ValueError:
        return None


# Converts text with the given type (int/float); returns None on failure.
def _to_number(value, kind):
    try:
        return kind(value)
    except (TypeError, ValueError):
        return None
