import pytest
from backend.app import app, db, users_collection, sessions_collection
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

# Test 2: Calendar View
def test_calendar_view(client, monkeypatch):
    def mock_find(query):
        return [
            {"_id": ObjectId(), "course": "Math", "date": "2023-12-10", "time": "10:00 AM", "timezone": "UTC"}
        ]
    
    monkeypatch.setattr(sessions_collection, "find", mock_find)

    response = client.get("/calendar")
    assert response.status_code == 200
    assert b"Your Calendar" in response.data
