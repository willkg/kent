# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
import gzip
import json
from logging.config import dictConfig
import os
from typing import Union
import uuid
import zlib

from flask import Flask, request, render_template

from kent import __version__


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s: %(name)s %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            },
        },
        "loggers": {
            "kent": {"level": "INFO"},
            "werkzeug": {"level": "ERROR"},
        },
        "root": {
            "level": "INFO",
            "handlers": ["wsgi"],
        },
    }
)


BANNER = None


@dataclass
class Event:
    project_id: int
    event_id: str

    # This is either a dict or a bytes depending on whether this is raven or
    # sentry-sdk
    payload: Union[dict, bytes]

    @property
    def summary(self):
        if not self.payload:
            return "no summary"

        if isinstance(self.payload, dict):
            # Sentry exceptions events
            exceptions = self.payload.get("exception", {}).get("values", [])
            if exceptions:
                first = exceptions[0]
                return f"{first['type']}: {first['value']}"

            # Sentry message
            msg = self.payload.get("message", None)
            if msg:
                return msg

            # CSP security report (older browsers)
            if "csp-report" in self.payload:
                directive = self.payload["csp-report"].get(
                    "violated-directive", "unknown"
                )
                summary = f"csp-report: {directive}"
                return summary

        elif isinstance(self.payload, list):
            # CSP security report (newer browsers)
            if self.payload[0].get("type") == "csp-violation":
                directives = []
                for section in self.payload:
                    directives.append(
                        section.get("body", {}).get("effectiveDirective", "unknown")
                    )

                all_directives = ", ".join(directives)
                summary = f"csp-report: {all_directives}"
                return summary

        return "no summary"

    @property
    def timestamp(self):
        if self.payload and isinstance(self.payload, dict):
            # NOTE(willkg): timestamp is a string
            return self.payload.get("timestamp", "none")

        return "none"

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "event_id": self.event_id,
            "payload": self.payload,
        }


class EventManager:
    MAX_EVENTS = 100

    def __init__(self):
        # List of Event instances
        self.events = []

    def add_event(self, event_id, project_id, payload):
        event = Event(project_id=project_id, event_id=event_id, payload=payload)
        self.events.append(event)

        while len(self.events) > self.MAX_EVENTS:
            self.events.pop(0)

    def get_event(self, event_id):
        for event in self.events:
            if event.event_id == event_id:
                return event
        return None

    def get_events(self):
        return self.events

    def flush(self):
        self.events = []


EVENTS = EventManager()


INTERESTING_HEADERS = [
    "User-Agent",
    "X-Sentry-Auth",
]


def deep_get(path, structure, default=None):
    node = structure
    for part in path.split("."):
        if part.startswith("["):
            index = int(part[1:-1])
            node = node[index]
        elif part in node:
            node = node[part]
        else:
            return default
    return node


def create_app(test_config=None):
    dev_mode = os.environ.get("KENT_DEV", "0") == "1"

    # Always start an app with an empty error manager
    EVENTS.flush()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")

    if test_config is not None:
        app.config.from_mapping(test_config)

    if BANNER:
        app.logger.info(BANNER)

    @app.route("/", methods=["GET"])
    def index_view():
        host = request.scheme + "://" + request.headers["host"]
        dsn = request.scheme + "://public@" + request.headers["host"] + "/1"

        return render_template(
            "index.html",
            host=host,
            dsn=dsn,
            events=EVENTS.get_events(),
            version=__version__,
        )

    @app.route("/api/event/<event_id>", methods=["GET"])
    def api_event_view(event_id):
        app.logger.info(f"GET /api/event/{event_id}")
        event = EVENTS.get_event(event_id)
        if event is None:
            return {"error": f"Event {event_id} not found"}, 404

        return event.to_dict()

    @app.route("/api/eventlist/", methods=["GET"])
    def api_event_list_view():
        app.logger.info("GET /api/eventlist/")
        event_ids = [event.event_id for event in EVENTS.get_events()]
        return {"events": event_ids}

    @app.route("/api/flush/", methods=["POST"])
    def api_flush_view():
        app.logger.info("POST /api/flush")
        EVENTS.flush()
        return {"success": True}

    def log_headers(dev_mode, error_id, headers):
        # Log headers
        if dev_mode:
            for key, val in headers.items():
                app.logger.info("%s: header: %s: %s", error_id, key, val)
        else:
            for key in INTERESTING_HEADERS:
                if key in headers:
                    app.logger.info(
                        "%s: header: %s: %s", error_id, key, request.headers[key]
                    )

    @app.route("/api/<int:project_id>/store/", methods=["POST"])
    def store_view(project_id):
        app.logger.info(f"POST /api/{project_id}/store/")
        event_id = str(uuid.uuid4())
        log_headers(dev_mode, event_id, request.headers)

        # Decompress it
        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(request.data)
        elif request.headers.get("content-encoding") == "deflate":
            body = zlib.decompress(request.data)
        else:
            body = request.data

        # JSON decode it
        try:
            json_body = json.loads(body)
        except Exception:
            app.logger.exception("%s: exception when JSON-decoding body.", event_id)
            app.logger.error("%s: %s", event_id, json_body)
            body = {"error": "Kent could not decode body; see logs"}
            raise

        EVENTS.add_event(event_id=event_id, project_id=project_id, payload=json_body)

        # Log interesting bits in the body
        if "exception" in json_body:
            app.logger.info(
                "%s: exception: %s %s",
                event_id,
                deep_get("exception.values.[0].type", json_body),
                deep_get("exception.values.[0].value", json_body),
            )
        if "message" in json_body:
            app.logger.info("%s: message: %s", event_id, deep_get("message", json_body))
        app.logger.info(
            "%s: sdk: %s %s",
            event_id,
            deep_get("sdk.name", json_body),
            deep_get("sdk.version", json_body),
        )

        # Log event url
        event_url = f"{request.scheme}://{request.headers['host']}/api/event/{event_id}"
        app.logger.info("%s: project id: %s", event_id, project_id)
        app.logger.info("%s: url: %s", event_id, event_url)

        return {"success": True}

    @app.route("/api/<int:project_id>/security/", methods=["POST"])
    def security_view(project_id):
        app.logger.info(f"POST /api/{project_id}/security/")
        event_id = str(uuid.uuid4())
        log_headers(dev_mode, event_id, request.headers)

        body = request.data

        # Decode the JSON payload
        try:
            json_body = json.loads(body)
        except Exception:
            app.logger.exception("%s: exception when JSON-decoding body.", event_id)
            app.logger.error("%s: %s", event_id, body)
            body = {"error": "Kent could not decode body; see logs"}
            raise

        EVENTS.add_event(event_id=event_id, project_id=project_id, payload=json_body)

        # Log interesting bits in the body
        for i, report in enumerate(json_body):
            if "type" in report:
                app.logger.info(
                    "%s: %s: type: %s",
                    event_id,
                    i,
                    report["type"],
                )
        app.logger.info(
            "%s: project id: %s",
            event_id,
            project_id,
        )

        # Log event url
        event_url = f"{request.scheme}://{request.headers['host']}/api/event/{event_id}"
        app.logger.info(
            "%s: url: %s",
            event_id,
            event_url,
        )

        return {"success": True}

    return app
