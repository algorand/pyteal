# PyTeal

[![Build Status](https://travis-ci.com/algorand/pyteal.svg?token=B9eSse5TZikdgKBemvq3&branch=master)](https://travis-ci.com/algorand/pyteal)

Python Language Binding for Teal


NOTE: This is still a prototype. DO NOT use it in production.

### Development Setup

Setup venv (one time):
 * `python3 -m venv venv`


Active venv:
 * `. venv/bin/activate.fish` (if your shell is fish)
 * `. venv/bin/activate` (if your shell is bash/zsh)


Pip install pyteal in aditable state
 * `pip install -e .`
 
Type checking using mypy
* `mypy pyteal`

Run tests:
* `pytest`
