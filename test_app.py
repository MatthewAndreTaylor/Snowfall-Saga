from lobby_service.app import create_app
from gameservices.trivia.app import app
from simple_websocket import Client, ConnectionClosed
import json
import multiprocessing
import pytest


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


def run_app():
    app_runner = create_app()
    app_runner.config["LOGIN_DISABLED"] = True
    app_runner.login_manager.init_app(app_runner)
    app_runner.run(port=5000)


def test_message_websocket():
    proc = multiprocessing.Process(target=run_app, daemon=True)
    proc.start()

    url = "ws://localhost:5000/message"
    ws = Client(url)
    message = {
        "type": "newMessage",
        "text": "Hello World",
        "id": 1,
        "name": "TestUser",
    }
    try:
        ws.send(json.dumps(message))
        event = ws.receive()
        data = json.loads(event)
        for k, v in message.items():
            assert data[k] == v
    except ConnectionClosed:
        ws.close()

    proc.terminate()
    proc.join()


@pytest.fixture
def trivia_client():
    with app.test_client() as trivia_client:
        yield trivia_client


def test_trivia_page(trivia_client):
    response = trivia_client.get("/trivia")
    assert response.status_code == 200
