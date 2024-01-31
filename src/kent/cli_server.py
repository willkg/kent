# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

import kent.app

from flask import cli


os.environ["FLASK_APP"] = "kent.app"


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

        # Convert any adapter to localhost
        if host == "0.0.0.0":
            host = "localhost"
        elif host == "::":
            host = "::1"

        if ":" in host:
            host = f"[{host}]"

        kent.app.BANNER = f"Listening on http://{host}:{port}/"


def main():
    maybe_show_banner()
    cli.main()
