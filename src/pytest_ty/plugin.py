import functools
import itertools
import json
import subprocess
import typing

import pytest
from ty import find_ty_bin

if typing.TYPE_CHECKING:  # pragma: no cover
    import pathlib


_TY_RESULTS_STASH_KEY = pytest.StashKey[dict[str, list[str]]]()
_TY_FAILURE_MARKER: typing.Final = "*"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("ty")
    group.addoption("--ty", action="store_true", help="enable type checking with ty")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ty: Tests which run ty.")


def pytest_collect_file(file_path: "pathlib.Path", parent: pytest.Collector) -> "TyFile | None":
    config = parent.config
    if not config.option.ty or file_path.suffix != ".py":
        return None

    return TyFile.from_parent(parent, path=file_path)


def pytest_collection_modifyitems(session: pytest.Session, items: list[pytest.Item]) -> None:
    config = session.config
    if not config.option.ty:
        return

    if any(isinstance(item, TyStatusItem) for item in items):
        return

    status_item = TyStatusItem.from_parent(session, name=TyStatusItem.name)
    items.append(status_item)


def _run_ty_once(config: pytest.Config) -> dict[str, list[str]]:
    if (results := config.stash.get(_TY_RESULTS_STASH_KEY, None)) is not None:
        return results

    command = [_ty_bin(), "check", "--output-format=gitlab"]
    results = {}

    try:
        subprocess.run(command, check=True, timeout=60, capture_output=True, cwd=config.rootpath)  # noqa: S603
    except subprocess.CalledProcessError as e:
        stdout = e.stdout.decode(errors="replace") if e.stdout else "[]"
        stderr = e.stderr.decode(errors="replace") if e.stderr else "<empty>"
        results = _parse_ty_output(stdout)
        if not results:
            msg = f"ty exited with code {e.returncode}, stdout: {stdout}, stderr: {stderr}"
            results = {_TY_FAILURE_MARKER: [msg]}
    except subprocess.TimeoutExpired as e:
        msg = "\n".join(
            [
                e.stdout.decode(errors="replace") if e.stdout else "",
                e.stderr.decode(errors="replace") if e.stderr else "",
            ]
        )
        if not msg.strip():
            msg = f"`ty check` timed out after {e.timeout} seconds while running: {' '.join(map(str, command))}"
        results = {_TY_FAILURE_MARKER: [msg]}

    config.stash[_TY_RESULTS_STASH_KEY] = results
    return results


def _parse_ty_output(output: str) -> dict[str, list[str]]:
    try:
        diagnostics = json.loads(output)
    except json.JSONDecodeError:
        return {}

    results: dict[str, list[str]] = {}
    for diag in diagnostics:
        path = diag.get("location", {}).get("path", "")
        if not path:
            continue
        line = diag["location"]["positions"]["begin"]["line"]
        column = diag["location"]["positions"]["begin"]["column"]
        description = diag.get("description", "<ty failure>")
        message = f"{path}:{line}:{column}: {description}"
        results.setdefault(path, []).append(message)

    return results


@functools.cache
def _ty_bin() -> str:
    return find_ty_bin()


class TyError(Exception):
    pass


class TyFile(pytest.File):
    def collect(self) -> "list[TyItem]":
        return [TyItem.from_parent(self, name=TyItem.name)]


class TyItem(pytest.Item):
    name = "ty"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_marker(TyItem.name)

    def runtest(self) -> None:
        results = _run_ty_once(self.config)

        file_key = str(self.path.relative_to(self.config.rootpath))
        errors = results.get(file_key, [])

        if errors:
            raise TyError("\n".join(errors))


class TyStatusItem(pytest.Item):
    name = "ty::status"

    def runtest(self) -> None:
        results = _run_ty_once(self.config)

        if not len(results):
            return

        if _TY_FAILURE_MARKER in results:
            raise TyError("\n".join(results[_TY_FAILURE_MARKER]))

        raise TyError("\n".join(itertools.chain.from_iterable(results.values())))
