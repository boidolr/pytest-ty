from unittest import mock

import pytest

from pytest_ty.plugin import set_stash


@pytest.fixture
def failing_test(pytester):
    pytester.makepyfile(
        test_ignored_file="""
        def test_failure() -> None:
            value: int = "1"
            assert True
    """
    )


@pytest.fixture
def passing_test(pytester):
    pytester.makepyfile("""
        def test_sth() -> None:
            assert True
    """)


@pytest.mark.usefixtures("passing_test")
def test_ty_skipped_if_disabled(pytester):
    """Make sure that `ty` does not run if plugin is disabled."""

    set_stash_mock = mock.MagicMock(spec=set_stash)
    mock.patch("pytest_ty.set_stash", set_stash_mock)

    result = pytester.runpytest("-p no:ty", "-v")

    set_stash_mock.assert_not_called()
    assert result.ret == 0


@pytest.mark.usefixtures("passing_test")
def test_ty_checking_passes(pytester):
    """Make sure that `ty` runs on code."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


@pytest.mark.usefixtures("failing_test")
def test_ty_checking_fails(pytester):
    """Make sure that `ty` runs on code and detects issues."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1


@pytest.mark.usefixtures("failing_test")
def test_ty_exclude_ignores_matching_file(pytester):
    """Make sure that configured excludes are respected."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1

    pytester.makepyprojecttoml("""
    [tool.ty.src]
    exclude = ["test_ignored_file.py"]
    """)

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


def test_help_message(pytester):
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(["ty:", "*--ty*enable type checking with ty"])
