# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys

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
        "kind", nargs="?", default="message", help="What kind of thing to post. ['message', 'error']",
    )

    args = parser.parse_args()

    init(args.dsn)

    if args.kind == "message":
        capture_message("test error capture")
        print(f"Message posted to: {args.dsn}")
    elif args.kind == "error":
        try:
            raise Exception
        except Exception as exc:
            capture_exception(exc)
        print(f"Error posted to: {args.dsn}")
    else:
        print(f"{args.kind!r} is not a valid kind.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
