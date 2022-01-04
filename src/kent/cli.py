# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from flask.cli import main as flask_main

os.environ["FLASK_APP"] = "kent.app"


def main():
    flask_main()
