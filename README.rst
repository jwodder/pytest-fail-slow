.. image:: http://www.repostatus.org/badges/latest/active.svg
    :target: http://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. image:: https://github.com/jwodder/pytest-fail-slow/workflows/Test/badge.svg?branch=master
    :target: https://github.com/jwodder/pytest-fail-slow/actions?workflow=Test
    :alt: CI Status

.. image:: https://codecov.io/gh/jwodder/pytest-fail-slow/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/pytest-fail-slow

.. image:: https://img.shields.io/pypi/pyversions/pytest-fail-slow.svg
    :target: https://pypi.org/project/pytest-fail-slow/

.. image:: https://img.shields.io/conda/vn/conda-forge/pytest-fail-slow.svg
    :target: https://anaconda.org/conda-forge/pytest-fail-slow
    :alt: Conda Version

.. image:: https://img.shields.io/github/license/jwodder/pytest-fail-slow.svg
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
``pytest-fail-slow`` requires Python 3.7 or higher and pytest 6.0 or higher.
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

In addition, the ``--fail-slow DURATION`` option can be passed to the
``pytest`` command to affect all tests in that run.  If ``--fail-slow`` is
given and a test has the ``fail_slow`` marker, the duration given by the marker
takes precedence for that test.

If a test fails due to being slow, pytest's output will include the test's
duration and the duration threshold, like so::

    ________________________________ test_func ________________________________
    Test passed but took too long to run: Duration 123.0s > 5.0s

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

In addition, the ``--fail-slow-setup DURATION`` option can be passed to the
``pytest`` command to affect all tests in that run.  If ``--fail-slow-setup``
is given and a test has the ``fail_slow_setupresou`` marker, the duration given
by the marker takes precedence for that test.

If the setup for a test takes too long to run, the test will be marked as
"errored," the test itself will not be run, and pytest's output will include
the setup stage's duration and the duration threshold, like so::

    _______________________ ERROR at setup of test_func _______________________
    Setup passed but took too long to run: Duration 123.0s > 5.0s

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
