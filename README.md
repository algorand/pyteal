![PyTeal logo](https://github.com/algorand/pyteal/blob/master/docs/pyteal.png?raw=true)


# PyTeal: Algorand Smart Contracts in Python

[![Build Status](https://travis-ci.com/algorand/pyteal.svg?branch=master)](https://travis-ci.com/algorand/pyteal)
[![PyPI version](https://badge.fury.io/py/pyteal.svg)](https://badge.fury.io/py/pyteal)
[![Documentation Status](https://readthedocs.org/projects/pyteal/badge/?version=latest)](https://pyteal.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

PyTeal is a Python language binding for [Algorand Smart Contracts (ASC1s)](https://developer.algorand.org/docs/features/asc1/). 

Algorand Smart Contracts are implemented using a new language that is stack-based, 
called [Transaction Execution Approval Language (TEAL)](https://developer.algorand.org/docs/features/asc1/teal/). 

However, TEAL is essentially an assembly language. With PyTeal, developers can express smart contract logic purely using Python. 
PyTeal provides high level, functional programming style abstractions over TEAL and does type checking at construction time.

### Install 

PyTeal requires Python version >= 3.6

* `pip3 install pyteal`

### Documentation

[PyTeal Docs](https://pyteal.readthedocs.io/)

### Run Demo

In PyTeal root directory:

* `jupyter notebook demo/Pyteal\ Demonstration.ipynb`


### Development Setup

Setup venv (one time):
 * `python3 -m venv venv`

Active venv:
 * `. venv/bin/activate.fish` (if your shell is fish)
 * `. venv/bin/activate` (if your shell is bash/zsh)

Pip install PyTeal in editable state
 * `pip install -e .`

Install dependencies :
* `pip3 install -r requirements.txt`
 
Type checking using mypy
* `mypy pyteal`

Run tests:
* `pytest`

Format code:
* `black .`
