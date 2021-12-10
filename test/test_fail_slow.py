import pytest


@pytest.mark.parametrize(
    "src,success,slow",
    [
        (
            "def test_func():\n    assert 2 + 2 == 4\n",
            True,
            False,
        ),
        (
            "from time import sleep\n"
            "def test_func():\n"
            "    sleep(10)\n"
            "    assert 2 + 2 == 4\n",
            True,
            True,
        ),
        (
            "def test_func():\n    assert 2 + 2 == 5\n",
            False,
            False,
        ),
        (
            "from time import sleep\n"
            "def test_func():\n"
            "    sleep(10)\n"
            "    assert 2 + 2 == 5\n",
            False,
            False,
        ),
    ],
)
def test_fail_slow(pytester, src: str, success: bool, slow: bool) -> None:
    pytester.makepyfile(test_func=src)
    result = pytester.runpytest()
    if success:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    result.stdout.no_fnmatch_line("*Test took too long to run*")

    result = pytester.runpytest("--fail-slow=5")
    if success and not slow:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    if slow:
        result.stdout.re_match_lines(
            [
                r"_+ test_func _+$",
                r"Test took too long to run: Duration \d+\.\d+s > 5\.\d+s$",
            ],
            consecutive=True,
        )
    else:
        result.stdout.no_fnmatch_line("*Test took too long to run*")
