pip:
	pip install -e .

pip-development: pip
	pip install -e.[development]

build-and-test: build black mypy test

build:
	python -m scripts.generate_init --check

black:
	black --check .


mypy:
	mypy pyteal tests

test-unit:
	pytest pyteal tests/unit

test-integration:
	pytest tests/integration

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal

flake8:
	flake8 pyteal tests

.PHONY: build