import os
import pymongo
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from calendar import Calendar, month_name
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Load environment variables from .env file
load_dotenv()

# Environment variable setup
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")
if SECRET_KEY == "your_secret_key":
    raise ValueError("SECRET_KEY is not set. Please set it in your .env file.")

# MongoDB connection
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["studySchedulerDB"]

    users_collection = db["users"]
    sessions_collection = db["sessions"]

    print("MongoDB connection successful")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

# Initialize Flask app
app = Flask(__name__, template_folder="../frontend/templates",
            static_folder="../frontend/static")
app.secret_key = SECRET_KEY

# Enable secure cookie settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # Set to False for local development without HTTPS
    SESSION_PERMANENT=False
)


@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('home.html')


@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("index.html", user=session["user"])


@app.route("/calendar", defaults={"month": None, "year": None})
def calendar_view(month=None, year=None):
    today = datetime.date.today()
    month = month or today.month
    year = year or today.year

    # Validate month and year inputs
    if not (1 <= month <= 12):
        flash("Invalid month.", "error")
        return redirect(url_for("index"))

    cal = Calendar().monthdayscalendar(year, month)
    days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    prev_month = (month - 1) if month > 1 else 12
    next_month = (month + 1) if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    sessions = list(sessions_collection.find(
        {"date": {"$regex": f"^{year}-{month:02}"}}))

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
        sessions=sessions,
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
            "participants": []
        }

        try:
            sessions_collection.insert_one(session_data)
            flash("Study session created successfully!", "success")
        except Exception as e:
            flash(f"Error creating session: {e}", "error")

        return redirect(url_for("calendar_view"))

    return render_template("create_session.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if users_collection.find_one({'username': username}):
            flash("User already exists!", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        try:
            hashed_password = generate_password_hash(password)
            users_collection.insert_one(
                {"username": username, "password": hashed_password})
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error during registration: {e}", "error")
    return render_template("register.html")


@app.route("/profile")
def profile():
    if "user" not in session:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for("login"))

    user = users_collection.find_one({"username": session["user"]})
    user_sessions = list(sessions_collection.find(
        {"participants": session["user"]}))
    user_availability = user.get("availability", [])

    return render_template(
        "profile.html",
        user={
            "username": user["username"],
            "availability": user_availability,
            "sessions": user_sessions,
        }
    )


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/edit-session", methods=["GET", "POST"])
@app.route("/edit-session/<session_id>", methods=["GET", "POST"])
def edit_session(session_id=None):
    if "user" not in session:
        flash("Please log in to edit a session.", "error")
        return redirect(url_for("login"))

    if session_id:
        try:
            session_data = sessions_collection.find_one(
                {"_id": ObjectId(session_id)})
        except Exception as e:
            flash(f"Error fetching session: {e}", "error")
            return redirect(url_for("calendar_view"))

        if not session_data:
            flash("Session not found.", "error")
            return redirect(url_for("calendar_view"))

        if request.method == "POST":
            updated_course = request.form.get("course")
            updated_date = request.form.get("date")
            updated_time = request.form.get("time")
            updated_timezone = request.form.get("timezone")

            # Validate inputs
            if not updated_course or not updated_date or not updated_time or not updated_timezone:
                flash("All fields are required to update the session.", "error")
                return render_template("edit_session.html", session=session_data)

            try:
                sessions_collection.update_one(
                    {"_id": ObjectId(session_id)},
                    {"$set": {
                        "course": updated_course,
                        "date": updated_date,
                        "time": updated_time,
                        "timezone": updated_timezone,
                    }}
                )
                flash("Session updated successfully!", "success")
                return redirect(url_for("calendar_view"))
            except Exception as e:
                flash(f"Error updating session: {e}", "error")

        return render_template("edit_session.html", session=session_data)

    # If no session_id is provided, show a list of user's sessions to edit
    user_sessions = list(sessions_collection.find(
        {"participants": session["user"]}))
    return render_template("edit_session_list.html", sessions=user_sessions)


@app.route("/join-session/<session_id>", methods=["POST"])
def join_session(session_id):
    if "user" not in session:
        flash("Please log in to join a session.", "error")
        return redirect(url_for("login"))

    try:
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$addToSet": {"participants": session["user"]}}
        )
        flash("You have joined the session!", "success")
    except Exception as e:
        flash(f"Error joining session: {e}", "error")

    return redirect(url_for("calendar_view"))


@app.route("/leave-session/<session_id>", methods=["POST"])
def leave_session(session_id):
    if "user" not in session:
        flash("Please log in to leave a session.", "error")
        return redirect(url_for("login"))

    try:
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$pull": {"participants": session["user"]}}
        )
        flash("You have left the session.", "success")
    except Exception as e:
        flash(f"Error leaving session: {e}", "error")

    return redirect(url_for("calendar_view"))


if __name__ == "__main__":
    app.run(debug=True)
