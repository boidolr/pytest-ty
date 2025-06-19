from subprocess import PIPE
from subprocess import Popen

from pytest import File
from pytest import Item
from pytest import skip
from pytest import StashKey
from ty.__main__ import find_ty_bin

HISTKEY = "ty/mtimes"
_MTIMES_STASH_KEY = StashKey[dict[str, float]]()


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


class TyError(Exception):
    pass


class TyFile(File):
    def collect(self):
        return [TyItem.from_parent(self, name=TyItem.name)]


class TyItem(Item):
    name = "ty"
    __ty = find_ty_bin()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_marker(TyItem.name)

    def setup(self):
        self._tymtime = self.fspath.mtime()

        if ty_mtimes := get_stash(self.config):
            old = ty_mtimes.get(str(self.fspath))
            if old == self._tymtime:
                skip("file previously passed ty checks")

    def runtest(self):
        self.handler(path=self.fspath)

        if ty_mtimes := get_stash(self.config):
            ty_mtimes[str(self.fspath)] = self._tymtime

    def reportinfo(self):
        return (self.fspath, None, "")

    def handler(self, path):
        command = [
            self.__ty,
            "check",
            path,
            "--output-format=full",
        ]
        child = Popen(command, stdout=PIPE, stderr=PIPE)  # noqa: S603
        stdout, _ = child.communicate()

        if child.returncode != 0:
            raise TyError(stdout.decode())


def get_stash(config):
    return config.stash.get(_MTIMES_STASH_KEY, default=None)


def set_stash(config, value):
    config.stash[_MTIMES_STASH_KEY] = value
