# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from importlib.metadata import version as metadata_version
import logging
from urllib.parse import urlparse
import sys

try:
    import requests
except ImportError:
    print("You need to have requests installed.")
    sys.exit(1)

try:
    from sentry_sdk import init, capture_exception, capture_message
except ImportError:
    print("You need to have sentry_sdk installed.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dsn", default="http://public@localhost:5000/1", help="SENTRY_DSN to use"
    )
    parser.add_argument(
        "kind",
        nargs="?",
        default="message",
        help=(
            "What kind of thing to post. ['message', 'error', 'loggingerror', "
            + "'security_csp_new', 'security_csp_old']"
        ),
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)
    init(args.dsn)

    print(f"DSN: {args.dsn}")
    print(f"Sentry-sdk version: {metadata_version('sentry_sdk')}")
    if args.kind == "message":
        capture_message("test error capture")
        print(f"Message posted to: {args.dsn}")
        return

    elif args.kind == "error":
        try:
            raise Exception("intentional exception")
        except Exception as exc:
            capture_exception(exc)
        print(f"Error posted to: {args.dsn}")
        return

    elif args.kind == "loggingerror":
        try:
            raise Exception("intentional exception")
        except Exception:
            logging.exception("intentional exception")
        print(f"Error posted to: {args.dsn}")
        return

    elif args.kind.startswith("security"):
        parsed = urlparse(args.dsn)
        report_uri = f"{parsed.scheme}://{parsed.username}@{parsed.netloc}/api{parsed.path}/security/"

        data = None

        if args.kind == "security_csp_new":
            # Newer browsers send this structure
            # From: https://w3c.github.io/reporting/#sample-reports
            data = [
                {
                    "age": 0,
                    "body": {
                        "blockedURL": "https://maps.googleapis.com/maps/api/js",
                        "disposition": "enforce",
                        "documentURL": "https://test.example.com/",
                        "effectiveDirective": "script-src",
                        "originalPolicy": (
                            "default-src 'self'; "
                            + "img-src 'self'; "
                            + "script-src 'self'; "
                            + "form-action 'self'; "
                            + "frame-ancestors 'self'; "
                            + "report-to csp-endpoint; "
                            + f"report-uri {report_uri}"
                        ),
                        "referrer": "",
                        "statusCode": 200,
                    },
                    "type": "csp-violation",
                    "url": "https://test.example.com/",
                    "user_agent": "Mozilla/5.0 (user agent)",
                }
            ]

        elif args.kind == "security_csp_old":
            # Older browsers send this structure
            data = {
                "csp-report": {
                    "blocked-uri": "https://www.youtube.com",
                    "disposition": "enforce",
                    "document-uri": "http://localhost:8000/test-page/",
                    "effective-directive": "frame-src",
                    "original-policy": (
                        "style-src 'self' 'unsafe-inline'; "
                        + "base-uri 'none'; "
                        + "media-src 'self'; "
                        + "object-src 'none'; "
                        + "child-src 'self'; "
                        + "img-src 'self' data: http://test.example.com/; "
                        + "font-src 'self'; "
                        + "default-src 'self'; "
                        + "connect-src 'self' http://test.example.com/; "
                        + "script-src 'self' http://test.example.com/; "
                        + "frame-src 'self'; "
                        + f"report-uri {report_uri}"
                    ),
                    "referrer": "",
                    "status-code": 0,
                    "violated-directive": "frame-src",
                }
            }

        if data:
            resp = requests.post(report_uri, json=data)
            resp.raise_for_status()
            print(f"Security report posted to: {report_uri}")
            return

    print(f"{args.kind!r} is not a valid kind.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
