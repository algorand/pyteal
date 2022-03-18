# Required for merging:

pip:
	pip install -r requirements.txt
	pip install -e .

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
	HAS_ALGOD=TRUE pytest tests/semantic_test.py