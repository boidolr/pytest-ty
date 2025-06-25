pytest-ty
[![Build Status](https://github.com/boidolr/pytest-ty/actions/workflows/main.yaml/badge.svg)](https://github.com/boidolr/pytest-ty/actions/workflows/main.yaml "See Build Status on GitHub Actions")
[![pypi](https://img.shields.io/pypi/v/pytest-ty.svg)](https://pypi.org/project/pytest-ty/ "See PyPI page")
![python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fboidolr%2Fpytest-ty%2Fmain%2Fpyproject.toml)
=========

A [`pytest`](https://github.com/pytest-dev/pytest) plugin to run the [`ty`](https://github.com/astral-sh/ty) type checker.


Configuration
------------

Configure `ty` in `pyproject.toml` or `ty.toml`,
see the [`ty` README](https://github.com/astral-sh/ty/blob/main/docs/README.md).


Installation
------------

You can install "pytest-ty" from [`PyPI`](https://pypi.org):

* `uv add --dev pytest-ty`
* `pip install pytest-ty`

Usage
-----

* Activate the plugin when running `pytest`: `pytest --ty`
* Activate via `pytest` configuration: `addopts = "--ty"`


License
-------

Distributed under the terms of the [`MIT`](https://opensource.org/licenses/MIT) license, "pytest-ty" is free and open source software
