import os
import sys

import pytest

pytest_plugins = "pytester"


def pytest_configure(config: pytest.Config) -> None:
    # provide fallback for Windows tmp_dir implementation of `pytest`
    if pytest.version_tuple[0] in (7, "7") and sys.platform == "win32":
        if not any(os.environ.get(n) for n in ("LOGNAME", "USER", "LNAME", "USERNAME")):
            os.environ["USERNAME"] = "tester"
