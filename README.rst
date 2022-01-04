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

Installing and running locally
------------------------------

1. Install Kent.

   You can install Kent from PyPI::

      pipx install kent

   You can install a REVISH ("main", branch name, commit, whatever) from
   GitHub::

      pipx install https://github.com/willkg/kent/archive/refs/heads/<REVISH>.zip

   You can install from a checked out version of this repository::

      pipx install .

2. Run Kent::

      kent-server run [-h HOST] [-p PORT]
      

Creating a Docker container and running that
--------------------------------------------

TBD
