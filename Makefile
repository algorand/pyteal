# Required for merging:

pip:
	pip install --upgrade pip
	pip install -e .[test]


build-and-test: build black mypy test

build:
	python -m scripts.generate_init --check

black:
	black --check .

mypy:
	mypy pyteal

test:
	pytest


# Extras:

coverage:
	pytest --cov-report html --cov=pyteal

blackbox:
	pytest tests/blackbox_test.py
	pytest tests/user_guide_test.py
