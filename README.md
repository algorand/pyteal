# PyTeal

[![Build Status](https://travis-ci.com/algorand/pyteal.svg?token=B9eSse5TZikdgKBemvq3&branch=master)](https://travis-ci.com/algorand/pyteal)

Python Language Binding for Teal

This code **hasn't been audited**. Use it at your own risk.

### Install 

pyteal requires python version >= 3.6

* `pip install -r requirements.txt`

### Run Demo

In pyteal root directory:

* `jupyter notebook demo/Pyteal\ Demonstration.ipynb`


### Development Setup

Setup venv (one time):
 * `python3 -m venv venv`


Active venv:
 * `. venv/bin/activate.fish` (if your shell is fish)
 * `. venv/bin/activate` (if your shell is bash/zsh)


Pip install pyteal in editable state
 * `pip install -e .`
 
Type checking using mypy
* `mypy pyteal`

Run tests:
* `pytest`
