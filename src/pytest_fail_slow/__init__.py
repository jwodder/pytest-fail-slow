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
from collections.abc import Generator, Mapping
import os
import platform
import re
import sys
import traceback
from typing import Union
import pytest

__version__ = "0.6.0"
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
    item.stash[setup_timeout_key] = get_fail_slow_timeout(
        item, "fail_slow_setup", "--fail-slow-setup"
    )
    item.stash[call_timeout_key] = get_fail_slow_timeout(
        item, "fail_slow", "--fail-slow"
    )


def get_fail_slow_timeout(
    item: pytest.Item, mark_name: str, option_name: str
) -> int | float | None:
    m = item.get_closest_marker(mark_name)
    if m is None:
        timeout = item.config.getoption(option_name)
        assert isinstance(timeout, (int, float)) or timeout is None
        return timeout
    try:
        (duration,) = m.args
    except ValueError:
        raise pytest.UsageError(
            f"@pytest.mark.{mark_name}() takes exactly one positional argument"
        )
    enabled = m.kwargs.get("enabled", True)
    if isinstance(enabled, str):
        enabled = evaluate_enabled(item, mark_name, enabled)
    if not enabled:
        return None
    return parse_duration(duration)


def evaluate_enabled(item: pytest.Item, mark_name: str, condition: str) -> bool:
    # Based on evaluate_condition() in _pytest/skipping.py
    ctx = {
        "os": os,
        "sys": sys,
        "platform": platform,
        "config": item.config,
    }
    for dictionary in reversed(
        item.ihook.pytest_markeval_namespace(config=item.config)
    ):
        if not isinstance(dictionary, Mapping):  # pragma: no cover
            raise ValueError(
                "pytest_markeval_namespace() needs to return a dict, got"
                f" {dictionary!r}"
            )
        ctx.update(dictionary)
    if hasattr(item, "obj"):
        ctx.update(item.obj.__globals__)
    try:
        filename = f"<{mark_name} enabled>"
        code = compile(condition, filename, "eval")
        return bool(eval(code, ctx))
    except SyntaxError as exc:
        msglines = [
            f"Error evaluating {mark_name!r} condition",
            "    " + condition,
            "    " + " " * (exc.offset or 0) + "^",
            "SyntaxError: invalid syntax",
        ]
        pytest.fail("\n".join(msglines), pytrace=False)
    except Exception as exc:
        msglines = [
            f"Error evaluating {mark_name!r} condition",
            "    " + condition,
            *traceback.format_exception_only(type(exc), exc),
        ]
        pytest.fail("\n".join(msglines), pytrace=False)


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
