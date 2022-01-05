====
Kent
====

Kent is a service for debugging and integration testing Sentry.

:Code:          https://github.com/willkg/kent/
:Issues:        https://github.com/willkg/kent/issues
:License:       MPL v2


Goals
=====

Goals of Kent:

1. make it possible to debug ``before_send`` and ``before_breadcrumb``
   sanitization code when using sentry-sdk
2. make it possible to debug other sentry error submission payload issues
3. make it possible to write integration tests against a fake sentry instance


Quick start
===========

Installing and running on your local machine
--------------------------------------------

1. Install Kent.

   You can install Kent from PyPI with pipx or pip or whatever::

      pipx install kent

   You can install a REVISH ("main", branch name, commit, whatever) from
   GitHub::

      pipx install https://github.com/willkg/kent/archive/refs/heads/<REVISH>.zip

   You can install from a checked out version of this repository::

      pipx install .

2. Run Kent::

      kent-server run [-h HOST] [-p PORT]
      

Running in a Docker container
-----------------------------

I'm using something like this::

    FROM python:3.10.1-alpine3.15

    WORKDIR /app/

    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1

    RUN pip install -U 'pip>=8' && \
        pip install --no-cache-dir 'kent==VERSION'

    USER guest

    ENTRYPOINT ["/usr/local/bin/kent-server"]
    CMD ["run"]


Replace ``VERSION`` with the version of Kent you want to use. See
https://pypi.org/project/kent for releases.

Then::

    $ docker build -t faksentry:latest .
    $ docker run --rm --publish 8000:8000 fakesentry:latest run --host 0.0.0.0 --port 8000


Things to know about Kent
=========================

Kent is the fakest of fake Sentry servers. It supports a single Sentry project
with id ``1``. You can set up a Sentry DSN to point to Kent and have your
application send errors.

Kent is a refined fake Sentry service and doesn't like fast food.

Kent will keep track of the last 100 it received in memory. Nothing is
persisted to disk.

You can access the list of errors and error data with your web browser by going
to Kent's index page.

You can also access it with the API. This is most useful for integration tests
that want to assert things about errors.

``/api/errorlist/``
    List of all errors in memory with a unique error id.

``/api/error/ERRORID``
    Retrieve the payload for a specific error by id.

Kent definitely works with:

* Python sentry-sdk client

I don't know about anything else. If you use Kent with another Sentry client,
add an issue with details or a pull request to update the README.
