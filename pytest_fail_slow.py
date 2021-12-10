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
