from functools import cache
from re import match
from subprocess import CalledProcessError
from subprocess import run
from subprocess import TimeoutExpired
from sys import version_info

from pytest import File
from pytest import Item
from pytest import StashKey
from ty.__main__ import find_ty_bin

if version_info < (3, 11):
    ty_file_regex = r"^ --> ([^:]+):\d+:\d+"
else:
    ty_file_regex = r"^ --> ([^:]++):\d++:\d++"

_TY_RESULTS_STASH_KEY = StashKey[dict[str, list[str]]]()


def pytest_addoption(parser):
    group = parser.getgroup("ty")
    group.addoption("--ty", action="store_true", help="enable type checking with ty")


def pytest_configure(config):
    config.addinivalue_line("markers", "ty: Tests which run ty.")


def pytest_collect_file(file_path, parent):
    config = parent.config
    if not config.option.ty or file_path.suffix != ".py":
        return None

    return TyFile.from_parent(parent, path=file_path)


def _run_ty_once(config) -> dict[str, list[str]]:
    if (results := config.stash.get(_TY_RESULTS_STASH_KEY)) is not None:
        return results

    command = [_ty_bin(), "check", "--output-format=full"]
    results = {}

    try:
        run(command, check=True, timeout=60, capture_output=True, cwd=config.rootpath)  # noqa: S603
    except CalledProcessError as e:
        output = e.stdout.decode(errors="replace") if e.stdout else ""
        results = _parse_ty_output(output)
    except TimeoutExpired as e:
        msg = "\n".join(
            [
                e.stdout.decode(errors="replace") if e.stdout else "",
                e.stderr.decode(errors="replace") if e.stderr else "",
            ]
        )
        results = {"*": [msg]}

    config.stash[_TY_RESULTS_STASH_KEY] = results
    return results


def _parse_ty_output(output: str) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    current_error = []
    current_file = None

    for line in output.split("\n"):
        if match := match(ty_file_regex, line):
            if current_error and current_file:
                results.setdefault(current_file, []).append("\n".join(current_error).strip())
            current_file = match.group(1)
            current_error = [line]
        elif current_file:
            current_error.append(line)

    if current_error and current_file:
        results.setdefault(current_file, []).append("\n".join(current_error).strip())

    return results


@cache
def _ty_bin():
    return find_ty_bin()


class TyError(Exception):
    pass


class TyFile(File):
    def collect(self):
        return [TyItem.from_parent(self, name=TyItem.name)]


class TyItem(Item):
    name = "ty"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_marker(TyItem.name)

    def runtest(self):
        results = _run_ty_once(self.config)
        file_key = str(self.path.relative_to(self.config.rootpath))
        errors = results.get(file_key, [])

        if errors:
            raise TyError("\n".join(errors))
