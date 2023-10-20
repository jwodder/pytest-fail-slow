"""
Fail tests that take too long to run

``pytest-fail-slow`` is a pytest_ plugin for making tests fail that take too
long to run.  It adds a ``--fail-slow DURATION`` command-line option to pytest
that causes any & all otherwise-passing tests that run for longer than the
given duration to be marked as failures, and it adds a
``@pytest.mark.fail_slow(DURATION)`` marker for making an individual test fail
if it runs for longer than the given duration.  If ``--fail-slow`` is given and
a test has the ``@fail_slow()`` marker, the duration given by the marker takes
precedence for that test.

Note that slow tests will still be run to completion; if you want them to
instead be stopped early, use pytest-timeout_.

.. _pytest: https://docs.pytest.org
.. _pytest-timeout: https://github.com/pytest-dev/pytest-timeout

A duration can be supplied to the ``--fail-slow`` option as either a bare
floating-point number of seconds or as a floating-point number followed by one
of the following units (case insensitive):

- ``h``, ``hour``, ``hours``
- ``m``, ``min``, ``mins``, ``minute``, ``minutes``
- ``s``, ``sec``, ``secs``, ``second``, ``seconds``
- ``ms``, ``milli``, ``millisec``, ``milliseconds``
- ``us``, ``μs``, ``micro``, ``microsec``, ``microseconds``

Durations passed to the ``@pytest.mark.fail_slow()`` marker can be either
ints/floats (for a number of seconds) or strings in the same format as passed
to ``--fail-slow``.

If ``pytest-fail-slow`` marks a test as a failure, the output will include the
test's duration and the duration threshold, like so::

    ________________________________ test_func ________________________________
    Test passed but took too long to run: Duration 123.0s > 5.0s

**Note:** Only the durations for tests themselves are taken into consideration.
If a test passes in less than the specified duration, but one or more fixture
setups/teardowns take longer than the duration, the test will still be marked
as passing.

Visit <https://github.com/jwodder/pytest-fail-slow> for more information.
"""

__version__ = "0.4.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "pytest-fail-slow@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/pytest-fail-slow"

from numbers import Number
import re
import pytest

TIME_UNITS = {
    "hour": 3600.0,
    "min": 60.0,
    "sec": 1.0,
    "ms": 0.001,
    "us": 0.000001,
}


def parse_duration(s) -> float:
    if isinstance(s, Number):
        return s
    m = re.search(
        r"""
        (?<=[\d\s.])
        (?:
            (?P<hour>h(ours?)?)
            |(?P<min>m(in(ute)?s?)?)
            |(?P<sec>s(ec(ond)?s?)?)
            |(?P<ms>m(illi)?s(ec(ond)?s?)?|milli)
            |(?P<us>(μ|u|micro)s(ec(ond)?s?)?|micro)
        )\s*$
    """,
        s,
        flags=re.I | re.X,
    )
    if m:
        (unit,) = [k for k, v in m.groupdict().items() if v is not None]
        mul = TIME_UNITS[unit.lower()]
        s = s[: m.start()]
    else:
        mul = 1.0
    return float(s) * mul


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "fail_slow(duration): Fail test if it takes more than this long to run",
    )
    config.addinivalue_line(
        "markers",
        (
            "fail_slow_setup(duration):"
            " Fail test if it takes more than this long to set up"
        ),
    )


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--fail-slow",
        type=parse_duration,
        metavar="DURATION",
        help="Fail tests that take more than this long to run",
    )
    parser.addoption(
        "--fail-slow-setup",
        type=parse_duration,
        metavar="DURATION",
        help="Fail tests that take more than this long to set up",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    if report is None or report.outcome != "passed":
        return
    if report.when == "setup":
        mark = item.get_closest_marker("fail_slow_setup")
        if mark is not None:
            if len(mark.args) != 1:
                raise pytest.UsageError(
                    "@pytest.mark.fail_slow_setup() takes exactly one argument"
                )
            timeout = parse_duration(mark.args[0])
        else:
            timeout = item.config.getoption("--fail-slow-setup")
        if timeout is not None and call.duration > timeout:
            report.outcome = "failed"
            report.longrepr = (
                "Setup passed but took too long to run:"
                f" Duration {call.duration}s > {timeout}s"
            )
    elif report.when == "call":
        mark = item.get_closest_marker("fail_slow")
        if mark is not None:
            if len(mark.args) != 1:
                raise pytest.UsageError(
                    "@pytest.mark.fail_slow() takes exactly one argument"
                )
            timeout = parse_duration(mark.args[0])
        else:
            timeout = item.config.getoption("--fail-slow")
        if timeout is not None and call.duration > timeout:
            report.outcome = "failed"
            report.longrepr = (
                "Test passed but took too long to run:"
                f" Duration {call.duration}s > {timeout}s"
            )
