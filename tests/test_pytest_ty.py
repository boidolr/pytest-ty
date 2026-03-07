import subprocess

import pytest


@pytest.fixture
def failing_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_failing_file="""
        def test_failure() -> None:
            value: int = "1"
            assert True
    """
    )


@pytest.fixture
def passing_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_passing_file="""
        def test_case() -> None:
            assert True
    """
    )


@pytest.fixture
def timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=[], timeout=1)

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.mark.usefixtures("passing_test")
def test_ty_skipped_if_disabled(pytester: pytest.Pytester) -> None:
    """Make sure that `ty` does not run if plugin is disabled."""

    pytester.makefile(".ini", pytest="[pytest]\naddopts=--ty\n")

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(["*::ty*"])
    assert result.ret == 0

    pytester.makefile(".ini", pytest="[pytest]\naddopts=-p no:ty\n")

    result = pytester.runpytest("-v")
    result.stdout.no_fnmatch_line("*::ty*")
    assert result.ret == 0


@pytest.mark.usefixtures("passing_test")
def test_ty_checking_passes(pytester: pytest.Pytester) -> None:
    """Make sure that `ty` runs on code."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


@pytest.mark.usefixtures("passing_test")
def test_ty_checking_passes_without_cache(pytester: pytest.Pytester) -> None:
    """Make sure that unavailable cache will not raise."""

    result = pytester.runpytest("--ty", "-v", "-pno:cacheprovider")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


@pytest.mark.usefixtures("failing_test")
def test_ty_checking_fails(pytester: pytest.Pytester) -> None:
    """Make sure that `ty` runs on code and detects issues."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1


@pytest.mark.usefixtures("failing_test")
def test_ty_exclude_ignores_matching_file(pytester: pytest.Pytester) -> None:
    """Make sure that configured excludes are respected."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1

    pytester.makepyprojecttoml("""
    [tool.ty.src]
    exclude = ["test_failing_file.py"]
    """)

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


@pytest.mark.usefixtures("failing_test")
def test_ty_config_disables_rule(pytester: pytest.Pytester) -> None:
    """Make sure that configured excludes are respected."""

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty FAILED*"])
    assert result.ret == 1

    pytester.makefile(".toml", ty='[rules]\ninvalid-assignment="ignore"\n')

    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    assert result.ret == 0


def test_ty_two_files_both_pass(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_file1="""
        def test_a() -> None:
            assert True
        """,
        test_file2="""
        def test_b() -> None:
            assert True
        """,
    )
    result = pytester.runpytest("--ty", "-v")
    result.stdout.fnmatch_lines(["*test_file1.py::ty PASSED*", "*test_file2.py::ty PASSED*"])
    result.stdout.no_fnmatch_line("*::ty FAILED*")
    assert result.ret == 0


@pytest.mark.usefixtures("passing_test", "failing_test")
def test_ty_two_files_one_fails(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*test_passing_file.py::ty PASSED*"])
    result.stdout.fnmatch_lines(["*test_failing_file.py::ty FAILED*"])
    assert result.ret == 1


def test_help_message(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(["ty:", "*--ty*enable type checking with ty"])


@pytest.mark.usefixtures("failing_test")
def test_status_item_shown_on_failure(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty::status FAILED*"])
    assert result.ret == 1


@pytest.mark.usefixtures("failing_test")
def test_status_item_includes_file_names(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*test_failing_file.py*"])
    assert result.ret == 1


@pytest.mark.usefixtures("passing_test")
def test_status_item_shown_on_pass(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty::status PASSED*"])
    assert result.ret == 0


@pytest.mark.usefixtures("passing_test", "timeout")
def test_timeout_handling_passing_check(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    result.stdout.fnmatch_lines(["*::ty::status FAILED*"])
    assert result.ret == 1


@pytest.mark.usefixtures("failing_test", "timeout")
def test_timeout_handling_failing_check(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--ty", "-v")

    result.stdout.fnmatch_lines(["*::ty PASSED*"])
    result.stdout.fnmatch_lines(["*::ty::status FAILED*"])
    assert result.ret == 1
