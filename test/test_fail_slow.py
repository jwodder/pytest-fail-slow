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
            "    sleep(5)\n"
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
            "    sleep(5)\n"
            "    assert 2 + 2 == 5\n",
            False,
            False,
        ),
        (
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def slow_setup():\n"
            "    sleep(3)\n"
            "    yield\n"
            "    sleep(3)\n"
            "\n"
            "def test_func(slow_setup):\n"
            "    assert 2 + 2 == 4\n",
            True,
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
    result.stdout.no_fnmatch_line("*Test passed but took too long to run*")

    result = pytester.runpytest("--fail-slow=2")
    if success and not slow:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    if slow:
        result.stdout.re_match_lines(
            [
                r"_+ test_func _+$",
                r"Test passed but took too long to run: Duration \d+\.\d+s > 2\.\d+s$",
            ],
            consecutive=True,
        )
    else:
        result.stdout.no_fnmatch_line("*Test passed but took too long to run*")

    result = pytester.runpytest("--fail-slow=0.0333m")
    if success and not slow:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    if slow:
        result.stdout.re_match_lines(
            [
                r"_+ test_func _+$",
                r"Test passed but took too long to run: Duration \d+\.\d+s > 1\.9\d+s$",
            ],
            consecutive=True,
        )
    else:
        result.stdout.no_fnmatch_line("*Test passed but took too long to run*")
