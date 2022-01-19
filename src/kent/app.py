# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
import gzip
import json
import uuid

from kent import __version__

from flask import Flask, request, render_template


@dataclass
class Error:
    project_id: int
    error_id: str
    payload: dict

    def get_timestamp(self):
        return self.payload.get("timestamp", "none")

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

    def add_error(self, project_id, payload):
        error_id = str(uuid.uuid4())
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


def create_app(test_config=None):
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
        for key, val in request.headers.items():
            app.logger.info(f"{key}: {val}")

        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(request.data)
        else:
            body = request.data

        if request.headers.get("content-type") == "application/json":
            body = json.loads(body)

        if body:
            ERRORS.add_error(project_id=project_id, payload=body)

        return {"success": True}

    return app
