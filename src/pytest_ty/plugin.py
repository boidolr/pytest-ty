from functools import cache
from subprocess import CalledProcessError
from subprocess import run
from subprocess import TimeoutExpired

from pytest import File
from pytest import Item
from pytest import skip
from pytest import StashKey
from ty.__main__ import find_ty_bin

HISTKEY = "ty/mtimes"
_MTIMES_STASH_KEY = StashKey[dict[str, int]]()


def pytest_addoption(parser):
    group = parser.getgroup("ty")
    group.addoption("--ty", action="store_true", help="enable type checking with ty")


def pytest_configure(config):
    config.addinivalue_line("markers", "ty: Tests which run ty.")

    if not config.option.ty or not hasattr(config, "cache"):
        return

    set_stash(config, config.cache.get(HISTKEY, {}))


def pytest_collect_file(file_path, parent):
    config = parent.config
    if not config.option.ty or file_path.suffix != ".py":
        return None

    return TyFile.from_parent(parent, path=file_path)


def pytest_sessionfinish(session, exitstatus):
    config = session.config

    if not config.option.ty or not hasattr(config, "cache"):
        return

    if not hasattr(config, "workerinput"):
        cache = config.cache.get(HISTKEY, {})
        cache.update(get_stash(config))
        config.cache.set(HISTKEY, cache)


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

    def setup(self):
        self._tymtime = self.path.stat().st_mtime_ns

        if ty_mtimes := get_stash(self.config):
            old = ty_mtimes.get(str(self.path))
            if old == self._tymtime:
                skip("file previously passed ty checks")

    def runtest(self):
        self.handler(path=self.path)

        if ty_mtimes := get_stash(self.config):
            ty_mtimes[str(self.path)] = self._tymtime

    def handler(self, path):
        command = [
            _ty_bin(),
            "check",
            "--output-format=full",
            "--force-exclude",
            str(path),
        ]
        try:
            run(command, check=True, timeout=15)  # noqa: S603
        except (CalledProcessError, TimeoutExpired) as e:
            msg = "\n".join(
                [
                    e.stdout.decode(errors="replace"),
                    e.stderr.decode(errors="replace"),
                ]
            )
            raise TyError(msg) from e


def get_stash(config):
    return config.stash.get(_MTIMES_STASH_KEY, default=None)


def set_stash(config, value):
    config.stash[_MTIMES_STASH_KEY] = value
