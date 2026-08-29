import functools
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, get_user_by_email, get_user_by_id, init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


@app.context_processor
def inject_current_user():
    if "user_id" not in session:
        return {"current_user": None}
    return {"current_user": get_user_by_id(session["user_id"])}


def login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


VALID_RANGES = {"all", "7d", "30d", "month", "custom"}
DATE_FORMAT = "%Y-%m-%d"


def resolve_date_range(range_value, start_value, end_value):
    """Resolve profile filter params into (start_date, end_date, error).
    start_date/end_date are 'YYYY-MM-DD' strings, or (None, None) for all-time.
    error is a friendly string or None. Never raises."""
    today = date.today()

    if range_value == "7d":
        return (today - timedelta(days=6)).isoformat(), today.isoformat(), None
    if range_value == "30d":
        return (today - timedelta(days=29)).isoformat(), today.isoformat(), None
    if range_value == "month":
        return today.replace(day=1).isoformat(), today.isoformat(), None
    if range_value == "custom":
        if not start_value or not end_value:
            return None, None, "Please choose both a start and end date for a custom range. Showing all-time results instead."
        try:
            start_date = datetime.strptime(start_value, DATE_FORMAT).date()
            end_date = datetime.strptime(end_value, DATE_FORMAT).date()
        except ValueError:
            return None, None, "That doesn't look like a valid date. Showing all-time results instead."
        if start_date > end_date:
            return None, None, "Start date must be on or before the end date. Showing all-time results instead."
        return start_date.isoformat(), end_date.isoformat(), None
    return None, None, None


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email:
        return render_template("register.html", error="Name and email are required.", name=name, email=email)
    if "@" not in email:
        return render_template("register.html", error="Please enter a valid email address.", name=name, email=email)
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)
    if get_user_by_email(email) is not None:
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    password_hash = generate_password_hash(password)
    try:
        create_user(name, email, password_hash)
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user_row = get_user_by_id(session["user_id"])
    name_parts = user_row["name"].split()
    initials = "".join(part[0] for part in name_parts[:2]).upper()
    created_at = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S")
    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "initials": initials,
        "member_since": created_at.strftime("%B %Y"),
    }
    selected_range = request.args.get("range", "all")
    if selected_range not in VALID_RANGES:
        selected_range = "all"
    start_input = request.args.get("start", "")
    end_input = request.args.get("end", "")

    start_date, end_date, range_error = resolve_date_range(selected_range, start_input, end_input)

    stats = get_summary_stats(session["user_id"], start_date, end_date)
    transactions = get_recent_transactions(session["user_id"], start_date, end_date)
    categories = get_category_breakdown(session["user_id"], start_date, end_date)
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        selected_range=selected_range,
        start_input=start_input,
        end_input=end_input,
        range_error=range_error,
    )


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


@app.route("/expenses/add")
@login_required
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
@login_required
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
