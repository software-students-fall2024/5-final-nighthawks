import os
import pymongo
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, request
from calendar import Calendar, month_name
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Environment variable setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

# MongoDB connection
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["studySchedulerDB"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Initialize Flask app
app = Flask(__name__)
# Ensure to set a secure secret key
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calendar/<int:month>/<int:year>")
@app.route("/calendar", defaults={"month": None, "year": None})
def calendar_view(month=None, year=None):
    today = datetime.date.today()
    month = month or today.month
    year = year or today.year

    cal = Calendar().monthdayscalendar(year, month)
    days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    prev_month = (month - 1) if month > 1 else 12
    next_month = (month + 1) if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    return render_template(
        "calendar.html",
        calendar_days=cal,
        days_of_week=days_of_week,
        month_name=month_name[month],
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/create-session", methods=["GET", "POST"])
def create_session():
    if request.method == "POST":
        course = request.form["course"]
        date = request.form["date"]
        time = request.form["time"]
        timezone = request.form["timezone"]

        session_data = {
            "course": course,
            "date": date,
            "time": time,
            "timezone": timezone,
        }

        try:
            db["sessions"].insert_one(session_data)
            flash("Study session created successfully!")
        except Exception as e:
            flash(f"Error creating session: {e}")

        return redirect(url_for("calendar_view"))

    return render_template("create_session.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db["users"].find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            flash("Login successful!")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        try:
            hashed_password = generate_password_hash(password)
            db["users"].insert_one(
                {"username": username, "password": hashed_password})
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error during registration: {e}")
    return render_template("register.html")


@app.route("/profile")
def profile():
    if "user" not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for("login"))

    user = session["user"]
    sessions = list(db["sessions"].find({"created_by": user}))
    return render_template("profile.html", user=user, sessions=sessions)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
