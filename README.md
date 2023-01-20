 <!-- markdownlint-disable-file MD041 -->

![PyTeal logo](https://github.com/algorand/pyteal/blob/master/docs/pyteal.png?raw=true)

# PyTeal: Algorand Smart Contracts in Python

[![Build Status](https://github.com/algorand/pyteal/actions/workflows/build.yml/badge.svg)](https://github.com/algorand/pyteal/actions)
[![PyPI version](https://badge.fury.io/py/pyteal.svg)](https://badge.fury.io/py/pyteal)
[![Documentation Status](https://readthedocs.org/projects/pyteal/badge/?version=latest)](https://pyteal.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

PyTeal is a Python language binding for [Algorand Smart Contracts (ASC1s)](https://developer.algorand.org/docs/features/asc1/).

Algorand Smart Contracts are implemented using a new language that is stack-based,
called [Transaction Execution Approval Language (TEAL)](https://developer.algorand.org/docs/features/asc1/teal/).

However, TEAL is essentially an assembly language. With PyTeal, developers can express smart contract logic purely using Python.
PyTeal provides high level, functional programming style abstractions over TEAL and does type checking at construction time.

## Install

PyTeal requires Python version >= 3.10.

If your operating system (OS) Python version < 3.10, we recommend:
* Rather than override the OS Python version, install Python  >= 3.10 alongside the OS Python version.
* Use [pyenv](https://github.com/pyenv/pyenv#installation) or similar tooling to manage multiple Python versions.

### Recommended: Install from PyPi

Install the latest official release from PyPi:

* `pip install pyteal`

### Install Latest Commit

If needed, it's possible to install directly from the latest commit on master to use unreleased features:

> **WARNING:** Unreleased code is experimental and may not be backwards compatible or function properly. Use extreme caution when installing PyTeal this way.

* `pip install git+https://github.com/algorand/pyteal`

## Documentation

* [PyTeal Docs](https://pyteal.readthedocs.io/)
* `docs/` ([README](docs/README.md)) contains raw docs.

## Development Setup

Setup venv (one time):

* `python3 -m venv venv`

Active venv:

* `. venv/bin/activate` (if your shell is bash/zsh)
* `. venv/bin/activate.fish` (if your shell is fish)

Pip install PyTeal in editable state with dependencies:

* `make setup-development`
* OR if you don't have `make` installed:
  * `pip install -e . && pip install -r requirements.txt`

Format code:

* `black .`

Lint using flake8:

* `flake8 docs examples pyteal scripts tests *.py`

Type checking using mypy:

* `mypy pyteal scripts`

Run unit tests:

* `pytest pyteal tests/unit`

Run integration tests (assumes a developer-mode `algod` is available on port 4001):

* `pytest tests/integration`

Stand up developer-mode algod on ports 4001, 4002 and `tealdbg` on port 9392 (assumes [Docker](https://www.docker.com/) is available on your system):

* `docker-compose up -d`

Tear down and clean up resources for the developer-mode algod stood up above:

* `docker-compose down`
