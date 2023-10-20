from __future__ import annotations
import pytest


@pytest.mark.parametrize(
    "args,decor,limitrgx",
    [
        (["--fail-slow-setup=2"], "", r"2\.\d+s"),
        (["--fail-slow-setup=2.0"], "", r"2\.\d+s"),
        (["--fail-slow-setup=0.0333m"], "", r"1\.9\d+s"),
        (["--fail-slow-setup=10"], "", None),
        ([], "@pytest.mark.fail_slow_setup(2)\n", r"2s"),
        ([], "@pytest.mark.fail_slow_setup(2.0)\n", r"2\.\d+s"),
        ([], "@pytest.mark.fail_slow_setup('0.0333m')\n", r"1\.9\d+s"),
        ([], "@pytest.mark.fail_slow_setup(10)\n", None),
        (["--fail-slow-setup=30"], "@pytest.mark.fail_slow_setup(2)\n", r"2s"),
        (["--fail-slow-setup=0.01"], "@pytest.mark.fail_slow_setup(2)\n", r"2s"),
        (["--fail-slow-setup=0.01"], "@pytest.mark.fail_slow_setup(10)\n", None),
    ],
)
def test_fail_slow_setup_threshold(
    pytester, args: list[str], decor: str, limitrgx: str | None
) -> None:
    pytester.makepyfile(
        test_func=(
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def slow_setup():\n"
            "    sleep(3)\n"
            "    yield\n"
            "    sleep(3)\n"
            "\n"
            f"{decor}def test_func(slow_setup):\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest(*args)
    if limitrgx is None:
        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*Setup passed but took too long to run*")
    else:
        result.assert_outcomes(errors=1)
        result.stdout.re_match_lines(
            [
                r"_+ ERROR at setup of test_func _+$",
                "Setup passed but took too long to run:"
                rf" Duration \d+\.\d+s > {limitrgx}$",
            ],
            consecutive=True,
        )


@pytest.mark.parametrize("threshold,limitrgx", [(4, "4s"), (10, None)])
def test_fail_slow_multi_setup(pytester, threshold: str, limitrgx: str | None) -> None:
    pytester.makepyfile(
        test_func=(
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def slow_setup():\n"
            "    sleep(2)\n"
            "\n"
            "@pytest.fixture\n"
            "def slower_setup():\n"
            "    sleep(3)\n"
            "\n"
            f"@pytest.mark.fail_slow_setup({threshold})\n"
            "def test_func(slow_setup, slower_setup):\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest()
    if limitrgx is None:
        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*Setup passed but took too long to run*")
    else:
        result.assert_outcomes(errors=1)
        result.stdout.re_match_lines(
            [
                r"_+ ERROR at setup of test_func _+$",
                "Setup passed but took too long to run:"
                rf" Duration \d+\.\d+s > {limitrgx}$",
            ],
            consecutive=True,
        )


@pytest.mark.parametrize("threshold,success", [(2, False), (5, True)])
def test_fail_slow_setup_skips_test(pytester, threshold: str, success: bool) -> None:
    pytester.makepyfile(
        test_func=(
            "from pathlib import Path\n"
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def slow_setup():\n"
            "    sleep(3)\n"
            "\n"
            f"@pytest.mark.fail_slow_setup({threshold})\n"
            "def test_func(slow_setup):\n"
            '    Path("test.txt").write_text("Tested\\n")\n'
        )
    )
    result = pytester.runpytest()
    if success:
        result.assert_outcomes(passed=1)
        assert (pytester.path / "test.txt").read_text() == "Tested\n"
    else:
        result.assert_outcomes(errors=1)
        assert not (pytester.path / "test.txt").exists()
