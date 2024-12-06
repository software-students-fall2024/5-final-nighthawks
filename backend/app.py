import os
import pymongo
from flask import Flask, render_template, request, jsonify
from calendar import Calendar, month_name
import datetime

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["studySchedulerDB"]
    users_collection = db["users"]
    study_groups_collection = db["study_groups"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

app = Flask(__name__)

"""
Users collection structure:
{
  "user_id": "12345",                         # Unique user identifier
  "name": "Sallie Mae",                       # Full name
  "email": "salliemae@example.com",           # email
  "institution": "NYU",                       # Institution name
  "timezone": "America/New_York",             # User's timezone
  "courses": ["Calculus I", "Life Science"],  # List of enrolled courses
  "availability": [                           # Weekly availability schedule
      {"day": "Monday", "start": "10:00", "end": "12:00"},
      {"day": "Wednesday", "start": "14:00", "end": "16:00"}
  ]
}

Study groups collection structure:
{
  "id": "67890",                       # Unique study group identifier
  "title": "Calc I Study Group",       # Name of the study group
  "course": "Calculus I",              # Associated course
  "institution": "NYU",                # Institution name
  "date": "2024-12-02",                # Date of the session (YYYY-MM-DD)
  "time": "10:00 AM",                  # Time of the session
  "attendees": 5                       # Current number of attendees
}
"""

@app.route("/")
@app.route("/calendar/<int:month>/<int:year>")
def calendar(month=None, year=None):
    today = datetime.date.today()
    month = month or today.month
    year = year or today.year

    cal = Calendar().monthdayscalendar(year, month)
    days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    prev_month = (month - 1) if month > 1 else 12
    next_month = (month + 1) if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    study_groups = list(study_groups_collection.find(
        {
            "date": {"$regex": f"^{year}-{month:02}"}
        },
        {"_id": 0}
    ))

    return render_template(
        "index.html",
        calendar_days=cal,
        days_of_week=days_of_week,
        month_name=month_name[month],
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        study_groups=study_groups,
    )

@app.route("/users", methods=["GET"])
def get_users():
    try:
        users = list(users_collection.find({}, {"_id": 0}))
        return jsonify(users)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/search", methods=["GET"])
def search_study_groups():
    course = request.args.get("course", "").strip()
    date = request.args.get("date", "").strip()

    query = {}
    if course:
        query["course"] = {"$regex": f"^{course}$", "$options": "i"}
    if date:
        query["date"] = date

    study_groups = list(study_groups_collection.find(query, {"_id": 0}))

    return render_template(
        "index.html",
        study_groups=study_groups,
    )

@app.route("/api/rsvp", methods=["POST"])
def rsvp():
    data = request.json
    group_id = data.get("groupId")
    response = data.get("response")

    if not group_id or response not in ["yes", "no"]:
        return jsonify({"error": "Invalid input"}), 400

    try:
        result = study_groups_collection.update_one(
            {"id": group_id},
            {"$inc": {"attendees": 1 if response == "yes" else -1}}
        )
        if result.modified_count == 0:
            return jsonify({"error": "Study group not found"}), 404
        return jsonify({"message": f"RSVP recorded: {response} for group {group_id}"})
    except Exception as e:
        print(f"Error updating RSVP: {e}")
        return jsonify({"error": "Database error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
