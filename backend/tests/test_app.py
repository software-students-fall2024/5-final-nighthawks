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