import pytest


@pytest.mark.parametrize(
    "src,success",
    [
        (
            "def test_func():\n    assert 2 + 2 == 4\n",
            True,
        ),
        (
            "from time import sleep\n"
            "def test_func():\n"
            "    sleep(10)\n"
            "    assert 2 + 2 == 4\n",
            False,
        ),
        (
            "def test_func():\n    assert 2 + 2 == 5\n",
            False,
        ),
        (
            "from time import sleep\n"
            "def test_func():\n"
            "    sleep(10)\n"
            "    assert 2 + 2 == 5\n",
            False,
        ),
    ],
)
def test_fail_slow(pytester, src: str, success: bool) -> None:
    pytester.makepyfile(test_func=src)
    result = pytester.runpytest("--fail-slow=5")
    if success:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
