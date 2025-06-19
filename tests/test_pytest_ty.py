from unittest import mock

from pytest_ty.plugin import set_stash


def test_no_ty_run_if_disabled(pytester):
    """Make sure that `ty` does not run if plugin is disabled."""

    pytester.makepyfile("""
        def test_sth() -> None:
            assert True
    """)
    set_stash_mock = mock.MagicMock(spec=set_stash)
    mock.patch("pytest_ty.set_stash", set_stash_mock)

    result = pytester.runpytest("-p no:ty", "-v")

    set_stash_mock.assert_not_called()
    assert result.ret == 0


def test_ty_checking_passes(pytester):
    """Make sure that `ty` runs on code."""

    pytester.makepyfile("""
        from pytest import mark

        @mark.parametrize("bar", ["test_value"])
        def test_sth(bar: str) -> None:
            assert bar == "test_value"
    """)

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


def test_ty_checking_fails(pytester):
    """Make sure that `ty` runs on code and detects issues."""

    pytester.makepyfile("""
        from pytest import mark

        @mark.parametrize("bar", ["test_value"])
        def test_sth(bar: str) -> str:
            assert bar == "test_value"
    """)

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1


def test_help_message(pytester):
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(["ty:", "*--ty*enable type checking with ty"])
