# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import socket

os.environ["FLASK_APP"] = "kent.app"

from flask.cli import main as flask_main  # noqa
from werkzeug import serving  # noqa


def mock_get_interface_ip(family):
    # NOTE(willkg): we do this weird thing becauwe werkzeug tries really hard
    # to be helpful when the host is 0.0.0.0 or something like that and if
    # you're running it in a docker container, it picks up the ip address of
    # the container which is really unhelpful.
    if family == socket.AF_INET:
        return "0.0.0.0"
    if family == socket.AF_INET6:
        return "::"


serving.get_interface_ip = mock_get_interface_ip


def main():
    flask_main()
