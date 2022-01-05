import pytest
import uuid

from kent.app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_index_view(client):
    resp = client.get("/")
    assert b"Kent" in resp.data


def test_store_view(client):
    resp = client.post("/api/1/store/", json={"id": "xyz"})
    assert resp.status_code == 200


def test_api_flush_view(client):
    resp = client.get("/api/flush/")
    assert resp.status_code == 200
    assert resp.json == {"success": True}


class TestAPIErrorListView:
    def test_empty_errorlist(self, client):
        resp = client.get("/api/errorlist/")
        assert resp.json == {"errors": []}

    def test_nonempty_errorlist(self, client):
        # Store an error
        resp = client.post("/api/1/store/", json={"id": "xyz"})
        assert resp.status_code == 200

        resp = client.get("/api/errorlist/")
        assert len(resp.json) == 1


class TestAPIErrorView:
    def test_404(self, client):
        error_id = str(uuid.uuid4())
        resp = client.get(f"/api/error/{error_id}")
        assert resp.status_code == 404
        assert resp.json == {"error": f"Error {error_id} not found"}

    def test_error_exists(self, client):
        error_payload = {"id": "new error"}

        # Store an error
        resp = client.post("/api/1/store/", json=error_payload)
        assert resp.status_code == 200

        # Get all the errors
        resp = client.get("/api/errorlist/")
        assert resp.status_code == 200
        error_id = resp.json["errors"][0]

        # Get the error by error_id
        resp = client.get(f"/api/error/{error_id}")
        assert resp.status_code == 200
        assert resp.json == {"error_id": error_id, "payload": error_payload}
