import pytest
from backend.app import app, db
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId


@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client


# Test 1: Home Endpoint
def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Study Scheduler" in response.data
    assert b"log in" in response.data
    assert b"register" in response.data

# Test 4: Calendar View
def test_calendar_view(client, monkeypatch):
    def mock_find(query):
        return [
            {"_id": ObjectId(), "course": "Math", "date": "2023-12-10", "time": "10:00 AM", "timezone": "UTC"}
        ]

    monkeypatch.setattr(db["sessions"], "find", mock_find)

    response = client.get("/calendar")
    assert response.status_code == 200
    assert b"Your Calendar" in response.data
    assert b"CS101" in response.data  # Matches the hardcoded session data


# Test 5: Create Session
def test_create_session(client, monkeypatch):
    def mock_insert_one(data):
        return {"inserted_id": ObjectId()}

    monkeypatch.setattr(db["sessions"], "insert_one", mock_insert_one)

    response = client.post(
        "/create-session",
        data={"course": "Math", "date": "2023-12-10", "time": "10:00 AM", "timezone": "UTC"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your Calendar" in response.data  # Ensure it redirects to the calendar view


# Test 6: Register Endpoint
def test_register(client, monkeypatch):
    def mock_insert_one(data):
        return {"inserted_id": ObjectId()}

    def mock_find_one(query):
        return None  # Simulate user not already existing

    monkeypatch.setattr(db["users"], "find_one", mock_find_one)
    monkeypatch.setattr(db["users"], "insert_one", mock_insert_one)

    response = client.post(
        "/register",
        data={"username": "new_user", "password": "password123", "confirm_password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login here" in response.data  # Check for login link in the register page


# Test 7: Failed Register (Existing User)
def test_register_existing_user(client, monkeypatch):
    def mock_find_one(query):
        return {"username": "existing_user"}  # Simulate user already exists

    monkeypatch.setattr(db["users"], "find_one", mock_find_one)

    response = client.post(
        "/register",
        data={"username": "existing_user", "password": "password123", "confirm_password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Register" in response.data  # Ensure it reloads the register page


# Test 8: Failed Register (Password Mismatch)
def test_register_password_mismatch(client):
    response = client.post(
        "/register",
        data={"username": "new_user", "password": "password123", "confirm_password": "password456"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Register" in response.data  # Ensure it reloads the register page
