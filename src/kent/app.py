# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
import gzip
import json
import logging
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
                "format": "[%(asctime)s] %(levelname)s: %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            },
        },
        "root": {
            "level": logging.INFO,
            "handlers": ["wsgi"],
        },
    }
)


@dataclass
class Error:
    project_id: int
    error_id: str

    # This is either a dict or a bytes depending on whether this is raven or
    # sentry-sdk
    payload: Union[dict, bytes]

    @property
    def summary(self):
        if not self.payload or not isinstance(self.payload, dict):
            return "no summary"

        exceptions = self.payload.get("exception", {}).get("values", [])
        if exceptions:
            first = exceptions[0]
            return f"{first['type']}: {first['value']}"

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
            "error_id": self.error_id,
            "payload": self.payload,
        }


class ErrorManager:
    MAX_ERRORS = 100

    def __init__(self):
        # List of Error instances
        self.errors = []

    def add_error(self, error_id, project_id, payload):
        error = Error(project_id=project_id, error_id=error_id, payload=payload)
        self.errors.append(error)

        while len(self.errors) > self.MAX_ERRORS:
            self.errors.pop(0)

    def get_error(self, error_id):
        for error in self.errors:
            if error.error_id == error_id:
                return error
        return None

    def get_errors(self):
        return self.errors

    def flush(self):
        self.errors = []


ERRORS = ErrorManager()


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
    ERRORS.flush()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")

    if test_config is not None:
        app.config.from_mapping(test_config)

    @app.route("/", methods=["GET"])
    def index_view():
        host = request.scheme + "://" + request.headers["host"]
        dsn = request.scheme + "://public@" + request.headers["host"] + "/1"

        return render_template(
            "index.html",
            host=host,
            dsn=dsn,
            errors=ERRORS.get_errors(),
            version=__version__,
        )

    @app.route("/api/error/<error_id>", methods=["GET"])
    def api_error_view(error_id):
        error = ERRORS.get_error(error_id)
        if error is None:
            return {"error": f"Error {error_id} not found"}, 404

        return error.to_dict()

    @app.route("/api/errorlist/", methods=["GET"])
    def api_error_list_view():
        error_ids = [error.error_id for error in ERRORS.get_errors()]
        return {"errors": error_ids}

    @app.route("/api/flush/", methods=["POST"])
    def api_flush_view():
        ERRORS.flush()
        return {"success": True}

    @app.route("/api/<int:project_id>/store/", methods=["POST"])
    def store_view(project_id):
        # Log headers
        if dev_mode:
            for key, val in request.headers.items():
                app.logger.info(f"header: {key}: {val!r}")
        else:
            for key in INTERESTING_HEADERS:
                if key in request.headers:
                    app.logger.info(f"{key}: {request.headers[key]}")

        # Decompress it
        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(request.data)
        elif request.headers.get("content-encoding") == "deflate":
            body = zlib.decompress(request.data)
        else:
            body = request.data

        # If it's JSON, then decode it
        try:
            body = json.loads(body)
        except Exception:
            app.logger.exception("exception when JSON-decoding body.")
            app.logger.error(body)
            body = {"error": "Kent could not decode body; see logs"}
            raise

        error_id = str(uuid.uuid4())
        ERRORS.add_error(error_id=error_id, project_id=project_id, payload=body)

        # Log interesting bits in the botdy
        app.logger.info("project id: %s", project_id)
        app.logger.info("event id: %s", error_id)
        if "exception" in body:
            app.logger.info(
                "exception: %s %s",
                deep_get("exception.values.[0].type", body),
                deep_get("exception.values.[0].value", body),
            )
        if "message" in body:
            app.logger.info("message: %s", deep_get("message", body))
        app.logger.info(
            "sdk: %s %s", deep_get("sdk.name", body), deep_get("sdk.version", body)
        )
        app.logger.info(
            "event url: %s://%s/api/error/%s",
            request.scheme,
            request.headers["host"],
            error_id,
        )

        return {"success": True}

    return app
