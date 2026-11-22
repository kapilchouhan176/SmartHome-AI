"""
routes/auth.py
Register (customer or provider), login and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from utils.database import fetch_one, execute, commit
from utils.helpers import dashboard_url, safe_next_url
from utils.validators import (is_valid_email, is_valid_phone, is_valid_password,
                              missing_fields, parse_experience)

auth_bp = Blueprint("auth", __name__)

REQUIRED = {"name": "Name", "email": "Email", "phone": "Phone", "city": "City", "password": "Password"}


# Shows the register form and creates a customer or provider account.
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(dashboard_url(g.user["role"]))
    form = request.form
    if request.method == "POST":
        errors = validate_register(form)
        if not errors:
            create_account(form)
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        for error in errors:
            flash(error, "danger")
    return render_template("register.html", form=form)


# Returns a list of problems with the register form (empty if valid).
def validate_register(form):
    errors = missing_fields(form, REQUIRED)
    if form.get("role") not in ("customer", "provider"):
        errors.append("Please choose Customer or Provider.")
    if form.get("email") and not is_valid_email(form["email"].strip()):
        errors.append("Please enter a valid email address.")
    if form.get("phone") and not is_valid_phone(form["phone"].strip()):
        errors.append("Phone number must be exactly 10 digits.")
    if not is_valid_password(form.get("password")):
        errors.append("Password must be at least 8 characters.")
    if form.get("password") != form.get("confirm_password"):
        errors.append("Passwords do not match.")
    if form.get("role") == "provider" and parse_experience(form.get("experience_years")) is None:
        errors.append("Experience must be a whole number between 0 and 60.")
    if not errors and email_taken(form["email"]):
        errors.append("An account with this email already exists.")
    return errors


# True if another account already uses this email.
def email_taken(email):
    return fetch_one("SELECT id FROM users WHERE email = %s", (email.strip().lower(),)) is not None


# Inserts the user row (and a pending providers row for providers).
def create_account(form):
    user_id = execute(
        """INSERT INTO users (name, email, password_hash, phone, role, city, address)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (form["name"].strip(), form["email"].strip().lower(),
         generate_password_hash(form["password"]), form["phone"].strip(),
         form["role"], form["city"].strip(), form.get("address", "").strip() or None),
        commit=False,
    )
    if form["role"] == "provider":
        execute(
            "INSERT INTO providers (user_id, bio, experience_years, city) VALUES (%s, %s, %s, %s)",
            (user_id, form.get("bio", "").strip() or None,
             parse_experience(form["experience_years"]), form["city"].strip()),
            commit=False,
        )
    commit()


# Checks email and password, then starts a fresh session.
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(dashboard_url(g.user["role"]))
    if request.method == "POST":
        user = check_login(request.form.get("email", ""), request.form.get("password", ""))
        if user:
            start_session(user)
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(safe_next_url(request.args.get("next")) or dashboard_url(user["role"]))
    return render_template("login.html", email=request.form.get("email", ""))


# Returns the user if the login is valid, otherwise flashes why and returns None.
def check_login(email, password):
    user = fetch_one("SELECT * FROM users WHERE email = %s", (email.strip().lower(),))
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Incorrect email or password.", "danger")
        return None
    if not user["is_active"]:
        flash("Your account has been deactivated. Please contact the admin.", "danger")
        return None
    return user


# Clears any old session and stores the user's id, role and name.
def start_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]


# Logs the user out (POST only, protected by CSRF).
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
