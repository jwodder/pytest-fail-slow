from __future__ import annotations
import pytest

CASES = [
    (
        "{decor}def test_func():\n    assert 2 + 2 == 4\n",
        True,
        False,
    ),
    (
        "from time import sleep\n"
        "{decor}def test_func():\n"
        "    sleep(5)\n"
        "    assert 2 + 2 == 4\n",
        True,
        True,
    ),
    (
        "{decor}def test_func():\n    assert 2 + 2 == 5\n",
        False,
        False,
    ),
    (
        "from time import sleep\n"
        "{decor}def test_func():\n"
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
        "{decor}def test_func(slow_setup):\n"
        "    assert 2 + 2 == 4\n",
        True,
        False,
    ),
]


@pytest.mark.parametrize("src,success,slow", CASES)
@pytest.mark.parametrize(
    "decor",
    [
        "",
        "import pytest\n@pytest.mark.fail_slow(2, enabled=False)\n",
        "import pytest\n@pytest.mark.fail_slow(2, enabled='1 == 2')\n",
    ],
)
def test_fail_slow_no_threshold(
    pytester: pytest.Pytester,
    src: str,
    success: bool,
    slow: bool,  # noqa: U100
    decor: str,
) -> None:
    pytester.makepyfile(test_func=src.format(decor=decor))
    result = pytester.runpytest()
    if success:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    result.stdout.no_fnmatch_line("*Test passed but took too long to run*")


@pytest.mark.parametrize("src,success,slow", CASES)
@pytest.mark.parametrize(
    "args,decor,limitrgx",
    [
        (["--fail-slow=2"], "", r"2\.\d+s"),
        (["--fail-slow=2.0"], "", r"2\.\d+s"),
        (["--fail-slow=0.0333m"], "", r"1\.9\d+s"),
        ([], "import pytest\n@pytest.mark.fail_slow(2)\n", r"2s"),
        ([], "import pytest\n@pytest.mark.fail_slow(2.0)\n", r"2\.\d+s"),
        ([], "import pytest\n@pytest.mark.fail_slow('0.0333m')\n", r"1\.9\d+s"),
        ([], "import pytest\n@pytest.mark.fail_slow(2, enabled=True)\n", r"2s"),
        ([], "import pytest\n@pytest.mark.fail_slow(2, enabled='1 == 1')\n", r"2s"),
        (["--fail-slow=30"], "import pytest\n@pytest.mark.fail_slow(2)\n", r"2s"),
        (["--fail-slow=0.01"], "import pytest\n@pytest.mark.fail_slow(2)\n", r"2s"),
    ],
)
def test_fail_slow_threshold(
    pytester: pytest.Pytester,
    src: str,
    success: bool,
    slow: bool,
    args: list[str],
    decor: str,
    limitrgx: str,
) -> None:
    pytester.makepyfile(test_func=src.format(decor=decor))
    result = pytester.runpytest(*args)
    if success and not slow:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)
    if slow:
        result.stdout.re_match_lines(
            [
                r"_+ test_func _+$",
                "Test passed but took too long to run:"
                rf" Duration \d+\.\d+s > {limitrgx}$",
            ],
            consecutive=True,
        )
    else:
        result.stdout.no_fnmatch_line("*Test passed but took too long to run*")


@pytest.mark.parametrize(
    "args", ["", "42, 'foo'", "enabled=False", "42, 'foo', enabled=False"]
)
def test_fail_slow_marker_bad_args(pytester: pytest.Pytester, args: str) -> None:
    pytester.makepyfile(
        test_func=(
            "import pytest\n"
            "\n"
            f"@pytest.mark.fail_slow({args})\n"
            "def test_func():\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        ["*UsageError: @pytest.mark.fail_slow() takes exactly one positional argument"]
    )


def test_fail_slow_disabled_plus_option(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_func=(
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.mark.fail_slow(2, enabled=False)\n"
            "def test_func():\n"
            "    sleep(5)\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest("--fail-slow=2")
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*Test passed but took too long to run*")


@pytest.mark.parametrize(
    "args,limitrgx",
    [
        ([], None),
        (["--fail-slow=0"], "2s"),
        (["--fail-slow=3"], "2s"),
    ],
)
def test_fail_slow_enabled_iff_option(
    pytester: pytest.Pytester, args: list[str], limitrgx: str | None
) -> None:
    pytester.makepyfile(
        test_func=(
            "from time import sleep\n"
            "import pytest\n"
            "\n"
            "@pytest.mark.fail_slow(2, enabled='config.getoption(\"--fail-slow\") is not None')\n"
            "def test_func():\n"
            "    sleep(5)\n"
            "    assert 2 + 2 == 4\n"
        )
    )
    result = pytester.runpytest(*args)
    if limitrgx is None:
        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*Test passed but took too long to run*")
    else:
        result.assert_outcomes(failed=1)
        result.stdout.re_match_lines(
            [
                r"_+ test_func _+$",
                "Test passed but took too long to run:"
                rf" Duration \d+\.\d+s > {limitrgx}$",
            ],
            consecutive=True,
        )


def test_fail_slow_bad_condition_syntax(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_func=(
            "import pytest\n"
            "\n"
            "@pytest.mark.fail_slow(2, enabled='bad syntax')\n"
            "def test_func():\n"
            '    Path("test.txt").write_text("Tested\\n")\n'
        )
    )
    result = pytester.runpytest("--fail-slow=2")
    result.assert_outcomes(errors=1)
    result.stdout.re_match_lines(
        [
            r"_+ ERROR at setup of test_func _+$",
            r"(invalid syntax(?:\. Perhaps you forgot a comma\?)?|unexpected EOF while parsing) \(<fail_slow enabled>, line 1\)",
            "",
            "During handling of the above exception, another exception occurred:",
            "Error evaluating 'fail_slow' condition",
            "    bad syntax",
            r" +\^",
            "SyntaxError: invalid syntax",
        ],
        consecutive=True,
    )
    assert not (pytester.path / "test.txt").exists()


def test_fail_slow_bad_condition(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_func=(
            "import pytest\n"
            "\n"
            "@pytest.mark.fail_slow(2, enabled='yes')\n"
            "def test_func():\n"
            '    Path("test.txt").write_text("Tested\\n")\n'
        )
    )
    result = pytester.runpytest("--fail-slow=2")
    result.assert_outcomes(errors=1)
    result.stdout.re_match_lines(
        [
            r"_+ ERROR at setup of test_func _+$",
            "name 'yes' is not defined",
            "",
            "During handling of the above exception, another exception occurred:",
            "Error evaluating 'fail_slow' condition",
            "    yes",
            "NameError: name 'yes' is not defined",
        ],
        consecutive=True,
    )
    assert not (pytester.path / "test.txt").exists()
