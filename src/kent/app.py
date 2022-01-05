# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import gzip
import json
import uuid

from kent import __version__

from flask import Flask, request, render_template


class ErrorManager:
    MAX_ERRORS = 100

    def __init__(self):
        self.errors = []

    def add_error(self, error):
        self.errors.append((str(uuid.uuid4()), error))
        while len(self.errors) > self.MAX_ERRORS:
            self.errors.pop(0)

    def get_error(self, error_id):
        for key, val in self.errors:
            if key == error_id:
                return val
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

        return {"error_id": error_id, "payload": error}

    @app.route("/api/errorlist/", methods=["GET"])
    def api_error_list_view():
        errors = [error_id for error_id, error in ERRORS.get_errors()]
        return {"errors": errors}

    @app.route("/api/flush/", methods=["GET"])
    def api_flush_view():
        ERRORS.flush()
        return {"success": True}

    @app.route("/api/1/store/", methods=["POST"])
    def store_view():
        for key, val in request.headers.items():
            app.logger.info(f"{key}: {val}")

        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(request.data)
        else:
            body = request.data

        if request.headers.get("content-type") == "application/json":
            body = json.loads(body)

        if body:
            ERRORS.add_error(body)
        return {"success": True}

    return app
