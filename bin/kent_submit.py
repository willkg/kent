#!/usr/bin/env python

# Usage: python bin/kent_submit.py [FILE]

import argparse
import json

import requests


def main():
    parser = argparse.ArgumentParser(description="submit sentry events to kent")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="8000")
    parser.add_argument("file", nargs="+", help="entry files to submit")

    args = parser.parse_args()

    for fn in args.file:
        with open(fn, "r") as fp:
            data = json.load(fp)

            if "payload" in data:
                data = data["payload"]

            print(f"Submitting {fn}...")
            resp = requests.post(
                f"http://{args.host}:{args.port}/api/0/store/", json=data
            )
            resp.raise_for_status()


if __name__ == "__main__":
    main()
