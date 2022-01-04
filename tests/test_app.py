import pytest

from kent.app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_index_view(client):
    resp = client.get("/")
    assert b"Kent" in resp.data
