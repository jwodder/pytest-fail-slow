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
        ([], "@pytest.mark.fail_slow_setup(2, enabled=True)\n", r"2s"),
        ([], "@pytest.mark.fail_slow_setup(2, enabled='1 == 1')\n", r"2s"),
        ([], "@pytest.mark.fail_slow_setup(2, enabled=False)\n", None),
        ([], "@pytest.mark.fail_slow_setup(2, enabled='1 == 2')\n", None),
        (
            ["--fail-slow-setup=2"],
            "@pytest.mark.fail_slow_setup(2, enabled=False)\n",
            None,
        ),
        (
            [],
            "@pytest.mark.fail_slow_setup(2, enabled='config.getoption(\"--fail-slow-setup\") is not None')\n",
            None,
        ),
        (
            ["--fail-slow-setup=0"],
            "@pytest.mark.fail_slow_setup(2, enabled='config.getoption(\"--fail-slow-setup\") is not None')\n",
            r"2s",
        ),
        (
            ["--fail-slow-setup=3"],
            "@pytest.mark.fail_slow_setup(2, enabled='config.getoption(\"--fail-slow-setup\") is not None')\n",
            r"2s",
        ),
        ([], "@pytest.mark.fail_slow_setup(10)\n", None),
        (["--fail-slow-setup=30"], "@pytest.mark.fail_slow_setup(2)\n", r"2s"),
        (["--fail-slow-setup=0.01"], "@pytest.mark.fail_slow_setup(2)\n", r"2s"),
        (["--fail-slow-setup=0.01"], "@pytest.mark.fail_slow_setup(10)\n", None),
    ],
)
def test_fail_slow_setup_threshold(
    pytester: pytest.Pytester, args: list[str], decor: str, limitrgx: str | None
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
def test_fail_slow_multi_setup(
    pytester: pytest.Pytester, threshold: str, limitrgx: str | None
) -> None:
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
def test_fail_slow_setup_skips_test(
    pytester: pytest.Pytester, threshold: str, success: bool
) -> None:
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


def test_fail_slow_setup_teardown_still_run(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_func=(
            "from pathlib import Path\n"
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def slow_setup():\n"
            "    sleep(3)\n"
            "    yield\n"
            '    Path("teardown.txt").write_text("Torn down\\n")\n'
            "\n"
            "@pytest.mark.fail_slow_setup(2)\n"
            "def test_func(slow_setup):\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    assert (pytester.path / "teardown.txt").read_text() == "Torn down\n"


def test_fail_slow_setup_all_run(pytester: pytest.Pytester) -> None:
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
            "@pytest.fixture\n"
            "def quick_setup():\n"
            '    Path("quick.txt").write_text("Set up\\n")\n'
            "\n"
            "@pytest.mark.fail_slow_setup(2)\n"
            "def test_func(slow_setup, quick_setup):\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    assert (pytester.path / "quick.txt").read_text() == "Set up\n"


@pytest.mark.parametrize(
    "args", ["", "42, 'foo'", "enabled=False", "42, 'foo', enabled=False"]
)
def test_fail_slow_setup_marker_bad_args(pytester: pytest.Pytester, args: str) -> None:
    pytester.makepyfile(
        test_func=(
            "import pytest\n"
            "\n"
            f"@pytest.mark.fail_slow_setup({args})\n"
            "def test_func():\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*UsageError: @pytest.mark.fail_slow_setup() takes exactly one"
            " positional argument"
        ]
    )
