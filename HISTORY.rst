=======
HISTORY
=======

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
