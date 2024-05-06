# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
            body=payload,
        )
        assert event.summary == expected


def test_index_view(client):
    resp = client.get("/")
    assert b"Kent" in resp.data


# From "kent-testpost" message with Python sentry-sdk 1.45.0
SENTRY_SDK_1_45_0_ERROR = {
    "breadcrumbs": {"values": []},
    "contexts": {
        "runtime": {
            "build": "3.10.14 (main, May  6 2024, 10:26:19) [GCC 13.2.0]",
            "name": "CPython",
            "version": "3.10.14",
        },
        "trace": {
            "parent_span_id": None,
            "span_id": "93e11289cc659ab8",
            "trace_id": "b7c12e7267ff4886a935914889833319",
        },
    },
    "environment": "production",
    "event_id": "9ae282ae03b6476ebeb1392a151edf55",
    "extra": {"sys.argv": ["/home/willkg/venvs/kent/bin/kent-testpost", "message"]},
    "level": "info",
    "message": "test error capture",
    "modules": {
        "blinker": "1.8.2",
        "certifi": "2024.2.2",
        "charset-normalizer": "3.3.2",
        "click": "8.1.7",
        "flask": "3.0.3",
        "idna": "3.7",
        "itsdangerous": "2.2.0",
        "jinja2": "3.1.4",
        "kent": "1.2.0",
        "markupsafe": "2.1.5",
        "pip": "24.0",
        "requests": "2.31.0",
        "sentry-sdk": "1.45.0",
        "setuptools": "69.5.1",
        "urllib3": "2.2.1",
        "werkzeug": "3.0.3",
        "wheel": "0.43.0",
    },
    "platform": "python",
    "release": "2667f04c7246db93ecbc175cf7a2534ad412154e",
    "sdk": {
        "integrations": [
            "argv",
            "atexit",
            "dedupe",
            "excepthook",
            "flask",
            "logging",
            "modules",
            "stdlib",
            "threading",
        ],
        "name": "sentry.python.flask",
        "packages": [{"name": "pypi:sentry-sdk", "version": "1.45.0"}],
        "version": "1.45.0",
    },
    "server_name": "saturn7",
    "timestamp": "2024-05-19T02:22:32.086845Z",
    "transaction_info": {},
}


def test_store_view(client):
    resp = client.post(
        "/api/1/store/",
        json=SENTRY_SDK_1_45_0_ERROR,
    )

    assert resp.status_code == 200


def test_envelope_view(client):
    resp = client.post(
        "/api/1/envelope/",
        content_type="application/octet-stream",
        # From "kent-testpost message" with Python sentry-sdk 2.2.0
        data=(
            b'{"event_id":"b5a2369b82c7421eb5c118a3151da03e","sent_at":"2024-05-19T03:13:43.016351Z","trace":{"trace_id":"e2a6aebaa043485e93cb5c8df6fbc230","environment":"production","release":"2667f04c7246db93ecbc175cf7a2534ad412154e","public_key":"public"}}\n{"type":"event","content_type":"application/json","length":1164}\n{"message":"test error capture","level":"info","event_id":"b5a2369b82c7421eb5c118a3151da03e","timestamp":"2024-05-19T03:13:43.015857Z","contexts":{"trace":{"trace_id":"e2a6aebaa043485e93cb5c8df6fbc230","span_id":"aa35c2671f716d4d","parent_span_id":null},"runtime":{"name":"CPython","version":"3.10.14","build":"3.10.14 (main, May  6 2024, 10:26:19) [GCC 13.2.0]"}},"transaction_info":{},"breadcrumbs":{"values":[]},"extra":{"sys.argv":["/home/willkg/venvs/kent/bin/kent-testpost","message"]},"modules":{"pip":"24.0","flask":"3.0.3","sentry-sdk":"2.2.0","wheel":"0.43.0","idna":"3.7","setuptools":"69.5.1","click":"8.1.7","blinker":"1.8.2","urllib3":"2.2.1","kent":"1.2.0","markupsafe":"2.1.5","werkzeug":"3.0.3","charset-normalizer":"3.3.2","itsdangerous":"2.2.0","requests":"2.31.0","jinja2":"3.1.4","certifi":"2024.2.2"},"release":"2667f04c7246db93ecbc175cf7a2534ad412154e","environment":"production","server_name":"saturn7","sdk":{"name":"sentry.python.flask","version":"2.2.0","packages":[{"name":"pypi:sentry-sdk","version":"2.2.0"}],"integrations":["argv","atexit","dedupe","excepthook","flask","logging","modules","stdlib","threading"]},"platform":"python"}\n'
        ),
    )
    assert resp.status_code == 200

    # Get all the events
    resp = client.get("/api/eventlist/")
    assert resp.status_code == 200
    event_id = resp.json["events"][0]["event_id"]

    # Get the event by event_id
    resp = client.get(f"/api/event/{event_id}")
    assert resp.status_code == 200
    assert resp.json == {
        "event_id": event_id,
        "payload": {
            "body": {
                "breadcrumbs": {
                    "values": [],
                },
                "contexts": {
                    "runtime": {
                        "build": "3.10.14 (main, May  6 2024, 10:26:19) [GCC 13.2.0]",
                        "name": "CPython",
                        "version": "3.10.14",
                    },
                    "trace": {
                        "parent_span_id": None,
                        "span_id": "aa35c2671f716d4d",
                        "trace_id": "e2a6aebaa043485e93cb5c8df6fbc230",
                    },
                },
                "environment": "production",
                "event_id": "b5a2369b82c7421eb5c118a3151da03e",
                "extra": {
                    "sys.argv": [
                        "/home/willkg/venvs/kent/bin/kent-testpost",
                        "message",
                    ],
                },
                "level": "info",
                "message": "test error capture",
                "modules": {
                    "blinker": "1.8.2",
                    "certifi": "2024.2.2",
                    "charset-normalizer": "3.3.2",
                    "click": "8.1.7",
                    "flask": "3.0.3",
                    "idna": "3.7",
                    "itsdangerous": "2.2.0",
                    "jinja2": "3.1.4",
                    "kent": "1.2.0",
                    "markupsafe": "2.1.5",
                    "pip": "24.0",
                    "requests": "2.31.0",
                    "sentry-sdk": "2.2.0",
                    "setuptools": "69.5.1",
                    "urllib3": "2.2.1",
                    "werkzeug": "3.0.3",
                    "wheel": "0.43.0",
                },
                "platform": "python",
                "release": "2667f04c7246db93ecbc175cf7a2534ad412154e",
                "sdk": {
                    "integrations": [
                        "argv",
                        "atexit",
                        "dedupe",
                        "excepthook",
                        "flask",
                        "logging",
                        "modules",
                        "stdlib",
                        "threading",
                    ],
                    "name": "sentry.python.flask",
                    "packages": [
                        {
                            "name": "pypi:sentry-sdk",
                            "version": "2.2.0",
                        },
                    ],
                    "version": "2.2.0",
                },
                "server_name": "saturn7",
                "timestamp": "2024-05-19T03:13:43.015857Z",
                "transaction_info": {},
            },
            "envelope_header": {
                "event_id": "b5a2369b82c7421eb5c118a3151da03e",
                "sent_at": "2024-05-19T03:13:43.016351Z",
                "trace": {
                    "environment": "production",
                    "public_key": "public",
                    "release": "2667f04c7246db93ecbc175cf7a2534ad412154e",
                    "trace_id": "e2a6aebaa043485e93cb5c8df6fbc230",
                },
            },
            "header": {
                "content_type": "application/json",
                "length": 1164,
                "type": "event",
            },
        },
        "project_id": 1,
    }


# From "kent-testpost security_csp_new"
CSP_REPORT_NEW = [
    {
        "age": 0,
        "body": {
            "blockedURL": "https://maps.googleapis.com/maps/api/js",
            "disposition": "enforce",
            "documentURL": "https://test.example.com/",
            "effectiveDirective": "script-src",
            "originalPolicy": "default-src 'self'; img-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'self'; report-to csp-endpoint; report-uri http://public@public@localhost:5000/api/1/security/",
            "referrer": "",
            "statusCode": 200,
        },
        "type": "csp-violation",
        "url": "https://test.example.com/",
        "user_agent": "Mozilla/5.0 (user agent)",
    }
]


def test_security_view(client):
    resp = client.post(
        "/api/1/security/",
        # From "kent-testpost security_csp_new"
        json=CSP_REPORT_NEW,
    )
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
        resp = client.post(
            "/api/1/store/",
            # From "kent-testpost" message with Python sentry-sdk 1.45.0
            json=SENTRY_SDK_1_45_0_ERROR,
        )

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
        # Store an event
        resp = client.post("/api/1/store/", json=SENTRY_SDK_1_45_0_ERROR)
        assert resp.status_code == 200

        # Get all the events
        resp = client.get("/api/eventlist/")
        assert resp.status_code == 200
        event_id = resp.json["events"][0]["event_id"]

        # Get the event by event_id
        resp = client.get(f"/api/event/{event_id}")
        assert resp.status_code == 200
        assert resp.json == {
            "project_id": 1,
            "event_id": event_id,
            "payload": {
                "envelope_header": None,
                "header": None,
                "body": SENTRY_SDK_1_45_0_ERROR,
            },
        }
