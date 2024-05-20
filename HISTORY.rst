=======
HISTORY
=======

2.0.0 (May 19th, 2024)
======================

Backwards incompatible changes:

* Changed ``/api/errorlist/`` to ``/api/eventlist/`` and changed response
  to a list of JSON objects with "error_id", "project_id", and "summary"
  keys.

  Example::

      curl http://localhost:5000/api/eventlist/
      {"events":[{"event_id":"1b1211bb-a113-480c-a3c9-0c7e7aea5e27","project
      _id":1,"summary":"test error capture"}]}

* Changed ``/api/error/ERROR_ID/`` to ``/api/event/EVENT_ID/`` and changed
  response so that the payload is now a JSON object with "envelope_header",
  "header", and "body" keys.

  If the event was captured using the ``store`` API, then "envelope_header" and
  "header" will be nulls and "body" will contain the payload.

  If the event was captured using the ``envelope`` API, then "envelope_header"
  will be the payload envelope header, "header" will be the item header, and
  "body" will be the item.

Changes:

* Feature: Support ``envelope`` API. (#42)
* Maintenance: Update to Flask 3. (#73)

Kent quietly stares off into the distance.


1.2.0 (January 31st, 2024)
==========================

Changes:

* Feature: Improve logging. (#69)
* Maintenance: Switch to ruff for formatting. (#66)

Kent found a rock shaped like two rocks.


1.1.0 (November 6th, 2023)
==========================

Changes:

* Feature: Support Python 3.12. (#50)
* Maintenance: Switch everything to ``pyproject.toml`` (#62)
* Feature: Add ``loggingerror`` to testpost command (#48)
* Maintenance: Drop support for Python 3.7. (#49)
* Feature: Rework app logging. All lines are now prefixed with the error id to
  make tracing easier.
* Feature: Add support for security reports like CSP security reports. (#59)

Kent wants to know if the sky is green sometimes.


1.0.0 (November 9th, 2022)
==========================

Fixes:

* Feature: Rework logging to be more helpful. (#32)
* Maintenance: Redid dev requirements.
* Feature: Support Python 3.11. (#33)

Kent is building a bird house and asked me for my popsicle stick.


0.5.0 (June 13th, 2022)
=======================

Fixes:

* Maintenance: Update pico.css to 1.5.3.
* Feature: Add Summary column. (#27)

Kent munched on popcorn quietly.


0.4.1 (March 29th, 2022)
========================

Fixes:

* Bug: kent-server didn't work with Flask 2.1.0. (#23)

Kent can make croissants disappear.


0.4.0 (January 24th, 2022)
==========================

Fixes:

* Bug: Fix handling so Kent works with raven-python which was deprecated many
  moons ago.

Kent handed me a cookie.


0.3.0 (January 19th, 2022)
==========================

Backwards incompatible changes:

* Changed ``/api/flush/`` from a GET to a POST.
* Changed response for ``/api/error/<ERRORID>`` to return a ``project_id`` key
  as well.

Fixes:

* Feature: Support multiple project ids. (#7)
* Feature: Add timestamp to event list. (#8)
* Feature: Add link to flush events to index page. (#9)

Kent eyed my slice of ice cream cake with interest.


0.2.0 (January 5th, 2022)
=========================

Bug fix release.

* Bug: Fix ``/api/errorlist/`` AttributeError bug. (#5)
* Feature: Add ``/api/flush/`` endpoint to flush the error manager. (#4)
* Add tests. (#1)
* Improve API docs.

Tried to feed Kent a banana. Kent peered at it and then put it down.


0.1.0 (January 4th, 2022)
=========================

Initial release with minimally viable feature set.

* Capture errors and keep them in memory.
* API endpoint to list errors.
* API endpoint to fetch error.

Fed Kent some pears. Kent loves pears.
