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


@app.route("/all-sessions", methods=["GET", "POST"])
def all_sessions():
    if "user" not in session:
        flash("Please log in to view sessions.", "error")
        return redirect(url_for("login"))

    try:
        # Handle session creation if POST request
        if request.method == "POST":
            new_session = {
                "course": request.form.get("course"),
                "date": request.form.get("date"),
                "time": request.form.get("time"),
                "timezone": request.form.get("timezone"),
                "user": session["user"],
                "participants": []
            }
            sessions_collection.insert_one(new_session)
            flash("New session created successfully!", "success")
            return redirect(url_for("all_sessions"))

        # Fetch all sessions
        sessions = list(sessions_collection.find())
        return render_template("all_sessions.html", sessions=sessions)

    except Exception as e:
        app.logger.error(f"All sessions error: {e}")
        flash("An error occurred while loading sessions.", "error")
        return redirect(url_for("index"))


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

    try:
        # Find sessions where the current user is a participant
        joined_sessions = list(sessions_collection.find(
            {"participants": session["user"]}
        ))
        return render_template("profile.html", joined_sessions=joined_sessions)

    except Exception as e:
        app.logger.error(f"Profile page error: {e}")
        flash("An error occurred while loading your profile.", "error")
        return redirect(url_for("index"))


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

    try:
        if session_id:
            # Validate ObjectId
            try:
                object_id = ObjectId(session_id)
            except (InvalidId, TypeError):
                flash("Invalid session ID.", "error")
                return redirect(url_for("calendar_view"))

            session_data = sessions_collection.find_one({"_id": object_id})

            if not session_data:
                flash("Session not found.", "error")
                return redirect(url_for("calendar_view"))

            # Ensure the user has permission to edit
            # You might want to add a check here to ensure only the session creator can edit
            if request.method == "POST":
                # Existing update logic
                try:
                    sessions_collection.update_one(
                        {"_id": object_id},
                        {"$set": {
                            "course": request.form.get("course"),
                            "date": request.form.get("date"),
                            "time": request.form.get("time"),
                            "timezone": request.form.get("timezone"),
                        }}
                    )
                    flash("Session updated successfully!", "success")
                    return redirect(url_for("calendar_view"))
                except Exception as e:
                    app.logger.error(f"Session update error: {e}")
                    flash("An error occurred while updating the session.", "error")

            return render_template("edit_session.html", session=session_data)

        # If no session_id, show list of user's sessions
        user_sessions = list(sessions_collection.find(
            {"participants": session["user"]}
        ))
        return render_template("edit_session_list.html", sessions=user_sessions)

    except Exception as e:
        app.logger.error(f"Edit session error: {e}")
        flash("An unexpected error occurred.", "error")
        return redirect(url_for("index"))


@app.route("/join-session/<session_id>", methods=["POST"])
def join_session(session_id):
    if "user" not in session:
        flash("Please log in to join a session.", "error")
        return redirect(url_for("login"))

    try:
        # Convert session_id to ObjectId
        object_id = ObjectId(session_id)

        # Add user to session participants
        result = sessions_collection.update_one(
            {"_id": object_id},
            {"$addToSet": {"participants": session["user"]}}
        )

        if result.modified_count:
            flash("You have joined the session!", "success")
        else:
            flash("Could not join the session.", "error")

        return redirect(url_for("all_sessions"))

    except Exception as e:
        app.logger.error(f"Join session error: {e}")
        flash("An error occurred while joining the session.", "error")
        return redirect(url_for("all_sessions"))


@app.route("/leave-session/<session_id>", methods=["POST"])
def leave_session(session_id):
    if "user" not in session:
        flash("Please log in to leave a session.", "error")
        return redirect(url_for("login"))

    try:
        # Convert session_id to ObjectId
        object_id = ObjectId(session_id)

        # Remove user from session participants
        result = sessions_collection.update_one(
            {"_id": object_id},
            {"$pull": {"participants": session["user"]}}
        )

        if result.modified_count:
            flash("You have left the session.", "success")
        else:
            flash("Could not leave the session.", "error")

        return redirect(url_for("all_sessions"))

    except Exception as e:
        app.logger.error(f"Leave session error: {e}")
        flash("An error occurred while leaving the session.", "error")
        return redirect(url_for("all_sessions"))


if __name__ == "__main__":
    app.run(debug=True)
