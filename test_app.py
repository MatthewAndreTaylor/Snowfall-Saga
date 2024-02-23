import pytest
from lobby_service.app import create_app
from gameservices.trivia.app import app
from gameservices.type_race.app import create_type_race_app


@pytest.fixture
def client():
    test_app = create_app()
    with test_app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    # The index page should redirect new users to login
    assert response.status_code == 302


def test_login(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data

    # Create a test user in the database
    response = client.post(
        "/register",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Attempt to log in with incorrect credentials
    response = client.post("/login", data={}, follow_redirects=True)
    assert response.status_code == 400

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "1234"},
        follow_redirects=True,
    )
    assert response.status_code == 401

    response = client.post(
        "/login", data={"username": "", "password": ""}, follow_redirects=True
    )
    assert response.status_code == 401

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200


@pytest.fixture
def trivia_client():
    with app.test_client() as trivia_client:
        yield trivia_client


def test_trivia_page(trivia_client):
    response = trivia_client.get("/trivia")
    assert response.status_code == 200


@pytest.fixture
def type_client():
    type_app = create_type_race_app()
    with type_app.test_client() as type_client:
        yield type_client


def test_type_connect(type_client):
    response = type_client.get("/type_race")
    assert response.status_code == 200
