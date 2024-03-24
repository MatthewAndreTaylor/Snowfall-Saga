from lobby_service.app import create_app
from gameservices.trivia.app import app
from gameservices.type_race.app import create_type_race_app
from lobby_service.app.messages import send_message
from lobby_service.app.store import process_purchase
import pytest
import json


@pytest.fixture
def client():
    """
    Fixture that creates a test client for the lobby service app
    """
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


class MockClient:
    """
    Mock client class for testing message sending and receiving
    """

    def __init__(self):
        self.counter = 0

    def send(self, message):
        message = json.loads(message)
        assert message["type"] == "newMessage"
        assert message["text"] == "Hello World"
        assert message["id"] == 1
        assert message["name"] == "TestUser"
        return message

    def receive(self):
        if self.counter == 0:
            self.counter += 1
            return json.dumps(
                {
                    "type": "newMessage",
                    "text": "Hello World",
                    "id": 1,
                    "name": "TestUser",
                }
            )
        else:
            raise ConnectionError

    def close(self):
        return


def test_message_websocket():
    message_client = MockClient()
    send_message(message_client, curr_user=None)


class MockPurchase:
    """
    Mock purchase class for purchasing sprites.
    """

    def __init__(self):
        self.counter = 0

    def send(self, message):
        message = json.loads(message)

        if self.counter <= 2:
            assert message["type"] == "purchaseSuccess"
            assert message["sprite"] == self.counter + 2
            assert message["points"] == 250 - 100 * self.counter
        else:
            assert message["type"] == "purchaseFailure"
            assert message["sprite"] == self.counter + 2
        return message

    def receive(self):
        if self.counter <= 2:
            self.counter += 1
            return json.dumps({"type": "purchase", "sprite": self.counter + 2})
        else:
            raise ConnectionError

    def close(self):
        return


def test_store_websocket(client):
    store_client = MockPurchase()
    process_purchase(store_client, curr_user=None)


@pytest.fixture
def trivia_client():
    """
    Fixture that creates a test client for the trivia app
    """
    with app.test_client() as trivia_client:
        yield trivia_client


def test_trivia_page(trivia_client):
    response = trivia_client.get("/")
    assert response.status_code == 200


@pytest.fixture
def type_client():
    type_app = create_type_race_app()
    with type_app.test_client() as type_client:
        yield type_client


def test_type_connect(type_client):
    response = type_client.get("/type_race")
    assert response.status_code == 200
