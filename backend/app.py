import os
import pymongo
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from calendar import Calendar, month_name
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Load environment variables from .env file
load_dotenv()

# Environment variable setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

# MongoDB connection
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["studySchedulerDB"]

    users_collection = db["users"]
    sessions_collection = db["sessions"]

    print("MongoDB connection successful")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Initialize Flask app
app = Flask(__name__, template_folder="../frontend/templates",
            static_folder="../frontend/static")
# Ensure to set a secure secret key
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")


@app.route('/')
def home():
    # If user is logged in, redirect to the index
    if 'user' in session:
        return redirect(url_for('index'))
    # else, have user log in
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
        }

        try:
            sessions_collection.insert_one(session_data)
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

        user = users_collection.find_one({"username": username})
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

        # Check if username already exists
        if users_collection.find_one({'username': username}):
            flash("User already exists!")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        try:
            hashed_password = generate_password_hash(password)
            users_collection.insert_one(
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
    flash("Logged out successfully.")
    return redirect(url_for("home"))


@app.route("/update-availability", methods=["GET", "POST"])
def update_availability():
    if "user" not in session:
        flash("Please log in to update your availability.")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Extract data from the form
        days = request.form.getlist("day[]")
        start_times = request.form.getlist("start_time[]")
        end_times = request.form.getlist("end_time[]")

        availability = [
            {"day": day, "start_time": start, "end_time": end}
            for day, start, end in zip(days, start_times, end_times)
        ]

        # Update user availability in database
        users_collection.update_one(
            {"username": session["user"]},  # Match the logged-in user
            {"$set": {"availability": availability}}
        )

        flash("Availability updated successfully!")
        return redirect(url_for("profile"))

    # Get current availability for user
    user = users_collection.find_one({"username": session["user"]})
    current_availability = user.get("availability", [])

    # Render template with current availability
    return render_template("update_availability.html", current_availability=current_availability)


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/join-session/<session_id>", methods=["POST"])
def join_session(session_id):
    if "user" not in session:
        flash("Please log in to join a session.")
        return redirect(url_for("login"))

    try:
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$addToSet": {"participants": session["user"]}}
        )
        flash("You have joined the session!")
    except Exception as e:
        flash(f"Error joining session: {e}")

    return redirect(url_for("calendar_view"))


@app.route("/leave-session/<session_id>", methods=["POST"])
def leave_session(session_id):
    if "user" not in session:
        flash("Please log in to leave a session.")
        return redirect(url_for("login"))

    try:
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$pull": {"participants": session["user"]}}
        )
        flash("You have left the session.")
    except Exception as e:
        flash(f"Error leaving session: {e}")

    return redirect(url_for("calendar_view"))
