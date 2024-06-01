|repostatus| |ci-status| |coverage| |pyversions| |conda| |license|

.. |repostatus| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. |ci-status| image:: https://github.com/jwodder/pytest-fail-slow/actions/workflows/test.yml/badge.svg
    :target: https://github.com/jwodder/pytest-fail-slow/actions/workflows/test.yml
    :alt: CI Status

.. |coverage| image:: https://codecov.io/gh/jwodder/pytest-fail-slow/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/pytest-fail-slow

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/pytest-fail-slow.svg
    :target: https://pypi.org/project/pytest-fail-slow/

.. |conda| image:: https://img.shields.io/conda/vn/conda-forge/pytest-fail-slow.svg
    :target: https://anaconda.org/conda-forge/pytest-fail-slow
    :alt: Conda Version

.. |license| image:: https://img.shields.io/github/license/jwodder/pytest-fail-slow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/pytest-fail-slow>`_
| `PyPI <https://pypi.org/project/pytest-fail-slow/>`_
| `Issues <https://github.com/jwodder/pytest-fail-slow/issues>`_
| `Changelog <https://github.com/jwodder/pytest-fail-slow/blob/master/CHANGELOG.md>`_

``pytest-fail-slow`` is a pytest_ plugin for treating tests as failed if they
took too long to run.  It adds markers for failing tests if they or their setup
stages run for longer than a given duration, along with command-line options
for applying the same cutoff to all tests.

Note that slow tests will still be run to completion; if you want them to
instead be stopped early, use pytest-timeout_.

.. _pytest: https://docs.pytest.org
.. _pytest-timeout: https://github.com/pytest-dev/pytest-timeout


Installation
============
``pytest-fail-slow`` requires Python 3.8 or higher and pytest 7.0 or higher.
Just use `pip <https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to
install it::

    python3 -m pip install pytest-fail-slow


Usage
=====

Failing Slow Tests
------------------

To cause a specific test to fail if it takes too long to run, apply the
``fail_slow`` marker to it, with the desired cutoff time as the argument:

.. code:: python

    import pytest

    @pytest.mark.fail_slow("5s")
    def test_something_sluggish():
        ...

If a test fails due to being slow, pytest's output will include the test's
duration and the duration threshold, like so::

    ________________________________ test_func ________________________________
    Test passed but took too long to run: Duration 123.0s > 5.0s

(*New in version 0.6.0*) If you only want a given test to fail for being slow
under certain conditions — say, when running under CI or on a certain platform
— supply the ``enabled`` keyword argument to the marker.  The value of
``enabled`` can be either a boolean expression or a `condition string`_.  When
the ``enabled`` value evaluates to ``True`` (the default), the test will fail
if its runtime exceeds the given duration; if it evaluates to ``False``, a
lengthy runtime will not cause the test to fail.  Example usage:

.. code:: python

    import os
    import pytest

    @pytest.mark.fail_slow("5s", enabled="CI" in os.environ)
    def test_something_that_needs_to_be_fast_in_ci():
        ...

An an alternative or in addition to the marker, the ``--fail-slow DURATION``
option can be passed to the ``pytest`` command to, in essence, apply the
``fail_slow`` marker with the given cutoff to all tests that don't already have
the marker.  (As far as ``pytest`` is concerned, the option does not actually
cause any markers to be added to any tests, in case your code cares about
that.)  If a test already has the ``fail_slow`` marker, the ``--fail-slow``
option will have no effect on it.

If you want a test to fail for being slow only if the ``--fail-slow`` option is
given, but you also want a different cutoff for the test than that passed to
the option, you can give the test a ``fail_slow`` marker that sets the desired
cutoff and also sets ``enabled`` to a condition string that checks whether
``--fail-slow`` has been given, like so:

.. code:: python

    import pytest

    @pytest.mark.fail_slow(3, enabled="config.getoption('--fail-slow') is not None")
    def test_something_sometimes_sluggish():
        ...

**Note:** This feature only takes the durations for tests themselves into
consideration.  If a test passes in less than the specified duration, but one
or more fixture setups/teardowns take longer than the duration, the test will
still be marked as passing.  To fail a test if the setup takes too long, see
below.


Failing Slow Setups
-------------------

*New in version 0.4.0*

To cause a specific test to fail if the setup steps for all of its fixtures
combined take too long to run, apply the ``fail_slow_setup`` marker to it, with
the desired cutoff time as the argument:

.. code:: python

    import pytest

    @pytest.mark.fail_slow_setup("5s")
    def test_costly_resource(slow_to_create):
        ...

Do not apply the marker to the test's fixtures; markers have no effect on
fixtures.

If the setup for a test takes too long to run, the test will be marked as
"errored," the test itself will not be run, and pytest's output will include
the setup stage's duration and the duration threshold, like so::

    _______________________ ERROR at setup of test_func _______________________
    Setup passed but took too long to run: Duration 123.0s > 5.0s

Like ``fail_slow``, the ``fail_slow_setup`` marker takes an optional
``enabled`` keyword argument that can be used to conditionally enable or
disable failure for slow setups.  There is also a ``--fail-slow-setup
DURATION`` option that can be passed to ``pytest`` to, in essence, apply the
marker to all tests that don't already have it.

**Note:** If a test depends on multiple fixtures and just one of them exceeds
the given duration on its own, the remaining fixtures will still have their
setup steps run.  Also, all fixture teardowns will still be run after the test
would have run.


Specifying Durations
--------------------

A duration passed to a marker or command-line option can be either a bare
number of seconds or else a floating-point number followed by one of the
following units (case insensitive):

- ``h``, ``hour``, ``hours``
- ``m``, ``min``, ``mins``, ``minute``, ``minutes``
- ``s``, ``sec``, ``secs``, ``second``, ``seconds``
- ``ms``, ``milli``, ``millisec``, ``milliseconds``
- ``us``, ``μs``, ``micro``, ``microsec``, ``microseconds``

.. _condition string: https://docs.pytest.org/en/8.2.x/historical-notes.html
                      #conditions-as-strings-instead-of-booleans
