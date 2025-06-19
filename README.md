pytest-ty [![Build Status](https://github.com/boidolr/pytest-ty/actions/workflows/main.yaml/badge.svg)](https://github.com/boidolr/pytest-ty/actions/workflows/main.yaml "See Build Status on GitHub Actions")
=========

A [`pytest`](https://github.com/pytest-dev/pytest) plugin to run the [`ty`](https://github.com/astral-sh/ty) type checker

----

This `pytest` plugin was generated with `Cookiecutter` along with `@hackebrot`'s `cookiecutter-pytest-plugin` template.


Features
--------

* Run `ty` checks on source code when executing `pytest`.


Configuration
------------

Configure `ty` in `pyproject.toml` or `ty.toml`,
see the [`ty` README](https://github.com/astral-sh/ty/blob/main/docs/README.md).


Installation
------------

You can install "pytest-ty" via `uv` from `GitHub`:

`uv add "pytest-ty @ git+https://github.com/boidolr/pytest-ty"`

Usage
-----

* Activate the plugin when running `pytest`: `pytest --ty`
* Activate via `pytest` configuration: `addopts = ["--ty"]`

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT` license, "pytest-ty" is free and open source software


Issues
------

If you encounter any problems, please `file an issue` along with a detailed description.

* `Cookiecutter`: https://github.com/audreyr/cookiecutter
* `@hackebrot`: https://github.com/hackebrot
* `MIT`: https://opensource.org/licenses/MIT
* `cookiecutter-pytest-plugin`: https://github.com/pytest-dev/cookiecutter-pytest-plugin
* `file an issue`: https://github.com/boidolr/pytest-ty/issues
* `pytest`: https://github.com/pytest-dev/pytest
* `tox`: https://tox.readthedocs.io/en/latest/
* `pip`: https://pypi.org/project/pip/
* `PyPI`: https://pypi.org/project
