"""
utils/decorators.py
Decorators that protect pages by login and by user role.
"""
from functools import wraps

from flask import g, flash, redirect, url_for, request, abort


# Sends visitors to the login page if nobody is logged in.
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("user") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


# Allows only the given roles; others get a 403 Forbidden page.
# Usage: @role_required("admin") or @role_required("customer", "provider")
def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if g.user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator
