pip:
	pip install -e .

pip-development: pip
	pip install -e.[development]

build-and-test: build black mypy test

build:
	python -m scripts.generate_init --check

black:
	black --check .

# currently not enforced on github
flake8:
	flake8 pyteal tests

mypy:
	mypy pyteal tests

test:
	pytest


# Extras:

coverage:
	pytest --cov-report html --cov=pyteal

blackbox:
	pytest tests/blackbox_test.py
	pytest tests/user_guide_test.py

.PHONY: build