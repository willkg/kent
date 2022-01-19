# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys

try:
    from sentry_sdk import init, capture_message
except ImportError:
    print("You need to have sentry_sdk installed.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dsn", default="http://public@localhost:5000/1", help="SENTRY_DSN to use"
    )

    args = parser.parse_args()

    init(args.dsn)

    capture_message("test error capture")
    print(f"Message posted to: {args.dsn}")


if __name__ == "__main__":
    main()
