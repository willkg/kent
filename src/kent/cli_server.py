# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import socket
import sys

import kent.app

from flask import cli  # noqa
from werkzeug import serving  # noqa


os.environ["FLASK_APP"] = "kent.app"


def mock_get_interface_ip(family):
    # NOTE(willkg): we do this weird thing becauwe werkzeug tries really hard
    # to be helpful when the host is 0.0.0.0 or something like that and if
    # you're running it in a docker container, it picks up the ip address of
    # the container which is really unhelpful.
    if family == socket.AF_INET:
        return "localhost"
    if family == socket.AF_INET6:
        return "::1"


serving.get_interface_ip = mock_get_interface_ip


# Prevent the Flask banner from showing
cli.show_server_banner = lambda *args, **kwargs: True


def maybe_show_banner():
    ctx = cli.cli.make_context(info_name=None, args=sys.argv)
    args = cli.cli.parse_args(ctx, args=sys.argv)
    if args[0] == "run":
        cmd = cli.cli.get_command(ctx, name="run")
        parser = cmd.make_parser(ctx)
        opts, _, _ = parser.parse_args(args[1:])
        port = opts.get("port", 5000)
        host = opts.get("host", "127.0.0.1")
        kent.app.BANNER = f"Listening on http://{host}:{port}/"


def main():
    maybe_show_banner()
    cli.main()
