"""
Fail tests that take too long to run

Visit <https://github.com/jwodder/pytest-fail-slow> for more information.
"""

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "pytest-fail-slow@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/pytest-fail-slow"

import pytest


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--fail-slow",
        type=float,
        help="Fail tests that take more than this many seconds to run",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    timeout = item.config.getoption("--fail-slow")
    if (
        report is not None
        and timeout is not None
        and report.when == "call"
        and report.outcome == "passed"
        and call.duration > timeout
    ):
        report.outcome = "failed"
        report.longrepr = (
            f"Test took too long to run: Duration {call.duration}s > {timeout}s"
        )
    return report
