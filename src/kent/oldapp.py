# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import re
import uuid
import sys
import gzip

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import path


settings.configure(
    DEBUG=True,
    SECRET_KEY="secretkey",
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=[
        "django_jinja",
    ],
    TEMPLATES=[
        {
            "BACKEND": "django_jinja.backend.Jinja2",
            "DIRS": [os.path.join(os.path.dirname(__file__), "jinja2")],
            "OPTIONS": {
                "match_extension": None,
                "undefined": "jinja2.Undefined",
                "extensions": [
                    "jinja2.ext.do",
                    "jinja2.ext.loopcontrols",
                    "jinja2.ext.i18n",
                    "django_jinja.builtins.extensions.DjangoFiltersExtension",
                ],
                "globals": {},
            },
        }
    ],
    ALLOWED_HOSTS=["*"],
    LOGGING={
        "version": 1,
        "handlers": {
            "console": {
                "level": logging.DEBUG,
                "class": "logging.StreamHandler",
                "formatter": "app",
            },
        },
        "loggers": {
            "django": {"handlers": ["console"], "level": logging.INFO},
            "django.server": {"handlers": ["console"], "level": logging.INFO},
            "django.request": {"handlers": ["console"], "level": logging.INFO},
            "fakesentry": {"handlers": ["console"], "level": logging.DEBUG},
        },
        "formatters": {
            "app": {"format": "%(asctime)s %(levelname)s - %(name)s - %(message)s"},
        },
    },
)


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


ERRORS = ErrorManager()
LOGGER = logging.getLogger("fakesentry")


def index_view(request):
    host = request.scheme + "://" + request.headers["host"]
    dsn = request.scheme + "://public@" + request.headers["host"] + "/1"
    return render(request, "index.html", context={"host": host, "dsn": dsn, "errors": ERRORS.get_errors()})


def store_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    for key, val in request.headers.items():
        LOGGER.info(f"{key}: {val}")

    if request.headers.get("content-encoding") == "gzip":
        body = gzip.decompress(request.body)
    else:
        body = request.body

    if request.headers.get("content-type") == "application/json":
        body = json.loads(body)

    if body:
        ERRORS.add_error(body)
    return render(request, "success.html")


def static_view(request, fn):
    goodchars = re.compile(r"^[A-Za-z0-9\.-]+$")
    if not goodchars.match(fn):
        LOGGER.info("404: bad chars {fn}")
        return HttpResponseNotFound()

    full_fn = os.path.join(os.path.dirname(__file__), "static", fn)
    if not os.path.exists(full_fn):
        LOGGER.info("404: doesn't exist {fn}")
        return HttpResponseNotFound()

    with open(full_fn, "rb") as fp:
        data = fp.read()

    content_types = {
        ".png": "image/png",
        ".css": "text/css",
    }

    content_type = content_types.get(os.path.splitext(fn)[1])
    if not content_type:
        LOGGER.info("404: no content type {fn}")
        return HttpResponseNotFound()

    return HttpResponse(content=data, content_type=content_type)


def api_error_view(request, error_id):
    error = ERRORS.get_error(error_id)
    if error is None:
        return JsonResponse({"error": f"Error {error_id} not found"}, status=404)

    return JsonResponse({"error_id": error_id, "error": error})


def api_error_list_view(request):
    return JsonResponse({"errors": ERRORS.keys()})


urlpatterns = [
    path(r"", index_view),
    path(r"api/error/<error_id>", api_error_view),
    path(r"api/errorlist/", api_error_list_view),
    # NOTE(willkg): this is hard-coded for project id 1
    path(r"api/1/store/", store_view),
    path(r"static/<fn>", static_view),
]


if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
