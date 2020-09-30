# PyTeal: Algorand Smart Contracts in Python

[![Build Status](https://travis-ci.com/algorand/pyteal.svg?branch=master)](https://travis-ci.com/algorand/pyteal)
[![PyPI version](https://badge.fury.io/py/pyteal.svg)](https://badge.fury.io/py/pyteal)
[![Documentation Status](https://readthedocs.org/projects/pyteal/badge/?version=latest)](https://pyteal.readthedocs.io/en/latest/?badge=latest)

PyTeal is a Python language binding for [Algorand Smart Contracts (ASC1s)](https://developer.algorand.org/docs/asc). 

Algorand Smart Contracts are implemented using a new language that is stack-based, 
called [Transaction Execution Approval Language (TEAL)](https://developer.algorand.org/docs/teal). 
This a non-Turing complete language that allows branch forwards but prevents recursive logic 
to maximize safety and performance. 

However, TEAL is essentially an assembly language. With PyTeal, developers can express smart contract logic purely using Python. 
PyTeal provides high level, functional programming style abstactions over TEAL and does type checking at construction time.

PyTeal **hasn't been security audited**. Use it at your own risk.

### Install 

pyteal requires python version >= 3.6

* `pip3 install pyteal`

### Documentation

[PyTeal Docs](https://pyteal.readthedocs.io/)

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
