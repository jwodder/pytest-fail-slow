"""
Fail tests that take too long to run

``pytest-fail-slow`` is a pytest_ plugin for treating tests as failed if they
took too long to run.  It adds markers for failing tests if they or their setup
stages run for longer than a given duration, along with command-line options
for applying the same cutoff to all tests.

Note that slow tests will still be run to completion; if you want them to
instead be stopped early, use pytest-timeout_.

.. _pytest: https://docs.pytest.org
.. _pytest-timeout: https://github.com/pytest-dev/pytest-timeout

Visit <https://github.com/jwodder/pytest-fail-slow> for more information.
"""

from __future__ import annotations
import re
from typing import Generator, Union
import pytest

__version__ = "0.5.0"
__author__ = "John Thorvald Wodder II"
__author_email__ = "pytest-fail-slow@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/pytest-fail-slow"

TIME_UNITS = {
    "hour": 3600.0,
    "min": 60.0,
    "sec": 1.0,
    "ms": 0.001,
    "us": 0.000001,
}

setup_timeout_key = pytest.StashKey[Union[int, float, None]]()
call_timeout_key = pytest.StashKey[Union[int, float, None]]()


def parse_duration(s: str | int | float) -> int | float:
    if isinstance(s, (int, float)):
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


def pytest_configure(config: pytest.Config) -> None:
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


def pytest_addoption(parser: pytest.Parser) -> None:
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


def pytest_runtest_setup(item: pytest.Item) -> None:
    setup_mark = item.get_closest_marker("fail_slow_setup")
    if setup_mark is not None:
        if len(setup_mark.args) != 1:
            raise pytest.UsageError(
                "@pytest.mark.fail_slow_setup() takes exactly one argument"
            )
        setup_timeout = parse_duration(setup_mark.args[0])
    else:
        setup_timeout = item.config.getoption("--fail-slow-setup")
    item.stash[setup_timeout_key] = setup_timeout

    call_mark = item.get_closest_marker("fail_slow")
    if call_mark is not None:
        if len(call_mark.args) != 1:
            raise pytest.UsageError(
                "@pytest.mark.fail_slow() takes exactly one argument"
            )
        call_timeout = parse_duration(call_mark.args[0])
    else:
        call_timeout = item.config.getoption("--fail-slow")
    item.stash[call_timeout_key] = call_timeout


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    if report.outcome != "passed":
        return report
    if report.when == "setup":
        timeout = item.stash[setup_timeout_key]
        if timeout is not None and call.duration > timeout:
            report.outcome = "failed"
            report.longrepr = (
                "Setup passed but took too long to run:"
                f" Duration {call.duration}s > {timeout}s"
            )
    elif report.when == "call":
        timeout = item.stash[call_timeout_key]
        if timeout is not None and call.duration > timeout:
            report.outcome = "failed"
            report.longrepr = (
                "Test passed but took too long to run:"
                f" Duration {call.duration}s > {timeout}s"
            )
    return report
