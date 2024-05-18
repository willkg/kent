import pytest
import uuid

from kent.app import create_app, Event


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


class TestEvent:
    @pytest.mark.parametrize(
        "payload, expected",
        [
            # Empty event payload
            ({}, "no summary"),
            # Event payload for an exception
            (
                {
                    "exception": {
                        "values": [
                            {"type": "Exception", "value": "Intentional exception"}
                        ]
                    }
                },
                "Exception: Intentional exception",
            ),
            # Message payload
            (
                {
                    "message": "some message",
                },
                "some message",
            ),
        ],
    )
    def test_summary(self, payload, expected):
        event = Event(
            project_id="0",
            event_id="9884b351-1e8f-4a28-8a9a-fc0033467e4e",
            payload=payload,
        )
        assert event.summary == expected


def test_index_view(client):
    resp = client.get("/")
    assert b"Kent" in resp.data


def test_store_view(client):
    resp = client.post("/api/1/store/", json={"id": "xyz"})
    assert resp.status_code == 200


def test_security_view(client):
    resp = client.post("/api/1/security/", json=[{"id": "xyz"}])
    assert resp.status_code == 200


def test_api_flush_view(client):
    resp = client.post("/api/flush/")
    assert resp.status_code == 200
    assert resp.json == {"success": True}


class TestAPIEventListView:
    def test_empty_eventlist(self, client):
        resp = client.get("/api/eventlist/")
        assert resp.json == {"events": []}

    def test_nonempty_eventlist(self, client):
        # Store an event
        resp = client.post("/api/1/store/", json={"id": "xyz"})
        assert resp.status_code == 200

        resp = client.get("/api/eventlist/")
        assert len(resp.json) == 1


class TestAPIEventView:
    def test_404(self, client):
        event_id = str(uuid.uuid4())
        resp = client.get(f"/api/event/{event_id}")
        assert resp.status_code == 404
        assert resp.json == {"error": f"Event {event_id} not found"}

    def test_event_exists(self, client):
        event_payload = {"id": "new event"}

        # Store an event
        resp = client.post("/api/1/store/", json=event_payload)
        assert resp.status_code == 200

        # Get all the events
        resp = client.get("/api/eventlist/")
        assert resp.status_code == 200
        event_id = resp.json["events"][0]

        # Get the event by event_id
        resp = client.get(f"/api/event/{event_id}")
        assert resp.status_code == 200
        assert resp.json == {
            "project_id": 1,
            "event_id": event_id,
            "payload": event_payload,
        }
