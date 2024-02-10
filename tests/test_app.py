import pytest
import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    # The index page should redirect new users to login
    assert response.status_code == 302
