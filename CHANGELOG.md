v0.6.0 (2024-06-01)
-------------------
- Add `enabled` keyword argument to markers

v0.5.0 (2024-02-11)
-------------------
- Migrated from setuptools to hatch
- Drop support for Python 3.7
- Don't cause an internal error on marker misuse with pluggy 1.4+
- Drop support for pytest 6
- Require pluggy 1.1+
- Add type-checking

v0.4.0 (2023-10-21)
-------------------
- Drop support for Python 3.6
- Support Python 3.11 and 3.12
- Added `@pytest.mark.fail_slow_setup()` marker and `--fail-slow-setup`
  command-line option for failing tests whose setups take too long to run

v0.3.0 (2022-08-12)
-------------------
- The `@pytest.mark.fail_slow()` marker now errors if not given exactly one
  argument.  Previously, it would either use the first argument or, if no
  arguments were given, it would be ignored.

v0.2.0 (2022-04-25)
-------------------
- Test against pytest 7
- Added `@pytest.mark.fail_slow(DURATION)` marker for making individual tests
  fail if they take too long to run

v0.1.0 (2021-12-10)
-------------------
Initial release
