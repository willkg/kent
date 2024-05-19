# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
import gzip
import json
import logging
from logging.config import dictConfig
import os
from typing import Optional, Union
import uuid
import zlib

from flask import Flask, request, render_template

from kent import __version__
from kent.utils import parse_envelope


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


def deep_get(structure, path, default=None):
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


@dataclass
class Event:
    project_id: int
    event_id: str

    # envelope_header when the envelope API is used
    envelope_header: Optional[dict] = None
    # item header
    header: Optional[dict] = None
    # item
    # attachments will be stored as bytes, non-attachments as python
    # datastructures
    body: Optional[Union[dict, bytes]] = None

    @property
    def summary(self):
        if not self.body:
            return "no summary"

        if isinstance(self.body, dict):
            # Kent body parsing errors
            kent_error = self.body.get("error")
            if kent_error:
                return kent_error

            # Sentry exceptions events
            exceptions = deep_get(self.body, "exception.values", default=[])
            if exceptions:
                first = exceptions[0]
                return f"{first['type']}: {first['value']}"

            # Sentry message
            msg = deep_get(self.body, "message", default=None)
            if msg:
                return msg

            # CSP security report (older browsers)
            if "csp-report" in self.body:
                directive = deep_get(
                    self.body, "csp-report.violated-directive", default="unknown"
                )
                summary = f"csp-report: {directive}"
                return summary

        elif isinstance(self.body, list):
            # CSP security report (newer browsers)
            if self.body[0].get("type") == "csp-violation":
                directives = []
                for section in self.body[0]:
                    directives.append(section.get("effectiveDirective") or "unknown")

                all_directives = ", ".join(directives)
                summary = f"csp-report: {all_directives}"
                return summary

        return "no summary"

    @property
    def timestamp(self):
        # NOTE(willkg): timestamp is a string
        return isinstance(self.body, dict) and self.body.get("timestamp") or "none"

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "event_id": self.event_id,
            "payload": {
                "envelope_header": self.envelope_header,
                "header": self.header,
                "body": self.body,
            },
        }


class EventManager:
    MAX_EVENTS = 100

    def __init__(self):
        # List of Event instances
        self.events = []

    def add_event(
        self, event_id, project_id, envelope_header=None, header=None, body=None
    ):
        event = Event(
            project_id=project_id,
            event_id=event_id,
            envelope_header=envelope_header,
            header=header,
            body=body,
        )
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

    if dev_mode:
        logging.getLogger("kent").setLevel(logging.DEBUG)
        app.logger.debug("Dev mode on.")

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
        event_ids = [
            {
                "project_id": event.project_id,
                "event_id": event.event_id,
                "summary": event.summary,
            }
            for event in EVENTS.get_events()
        ]
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

        app.logger.debug(f"{body}")

        # JSON decode it
        try:
            json_body = json.loads(body)
        except Exception:
            app.logger.exception("%s: exception when JSON-decoding body.", event_id)
            app.logger.error("%s: %s", event_id, json_body)
            EVENTS.add_event(
                event_id=event_id,
                project_id=project_id,
                body={"error": "Kent could not decode body; see logs"},
            )
            raise

        EVENTS.add_event(event_id=event_id, project_id=project_id, body=json_body)

        # Log interesting bits in the body
        if "exception" in json_body:
            app.logger.info(
                "%s: exception: %s %s",
                event_id,
                deep_get(json_body, "exception.values.[0].type"),
                deep_get(json_body, "exception.values.[0].value"),
            )
        if "message" in json_body:
            app.logger.info("%s: message: %s", event_id, deep_get(json_body, "message"))
        app.logger.info(
            "%s: sdk: %s %s",
            event_id,
            deep_get(json_body, "sdk.name"),
            deep_get(json_body, "sdk.version"),
        )

        # Log event url
        event_url = f"{request.scheme}://{request.headers['host']}/api/event/{event_id}"
        app.logger.info("%s: project id: %s", event_id, project_id)
        app.logger.info("%s: url: %s", event_id, event_url)

        return {"success": True}

    @app.route("/api/<int:project_id>/envelope/", methods=["POST"])
    def envelope_view(project_id):
        app.logger.info(f"POST /api/{project_id}/envelope/")
        request_id = str(uuid.uuid4())
        log_headers(dev_mode, request_id, request.headers)

        # Decompress it
        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(request.data)
        elif request.headers.get("content-encoding") == "deflate":
            body = zlib.decompress(request.data)
        else:
            body = request.data

        app.logger.debug(f"{body}")

        for item in parse_envelope(body):
            event_id = str(uuid.uuid4())
            EVENTS.add_event(
                event_id=event_id,
                project_id=project_id,
                envelope_header=item.envelope_header,
                header=item.header,
                body=item.body,
            )

            # Log interesting bits in the body
            if "exception" in item.body:
                app.logger.info(
                    "%s: exception: %s %s",
                    event_id,
                    deep_get(item.body, "exception.values.[0].type"),
                    deep_get(item.body, "exception.values.[0].value"),
                )
            if "message" in item.body:
                app.logger.info(
                    "%s: message: %s", event_id, deep_get(item.body, "message")
                )
            app.logger.info(
                "%s: sdk: %s %s",
                event_id,
                deep_get(item.body, "sdk.name"),
                deep_get(item.body, "sdk.version"),
            )

            # Log event url
            event_url = (
                f"{request.scheme}://{request.headers['host']}/api/event/{event_id}"
            )
            app.logger.info("%s: project id: %s", event_id, project_id)
            app.logger.info("%s: url: %s", event_id, event_url)

        return {"success": True}

    @app.route("/api/<int:project_id>/security/", methods=["POST"])
    def security_view(project_id):
        app.logger.info(f"POST /api/{project_id}/security/")
        event_id = str(uuid.uuid4())
        log_headers(dev_mode, event_id, request.headers)

        body = request.data

        app.logger.debug(f"{body}")

        # Decode the JSON payload
        try:
            json_body = json.loads(body)
        except Exception:
            app.logger.exception("%s: exception when JSON-decoding body.", event_id)
            app.logger.error("%s: %s", event_id, body)
            EVENTS.add_event(
                event_id=event_id,
                project_id=project_id,
                body={"error": "Kent could not decode body; see logs"},
            )
            raise

        EVENTS.add_event(event_id=event_id, project_id=project_id, body=json_body)

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
