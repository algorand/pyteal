pip:
	pip install -e .

pip-development: pip
	pip install -e.[development]

pip-docs: pip-development
	pip install -r docs/requirements.txt
	pip install doc2dash

pip-wheel:
	pip install wheel

bdist-wheel:
	python setup.py sdist bdist_wheel

docs:
	cd docs && \
    make html && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

build:
	python -m scripts.generate_init --check

black:
	black --check .

mypy:
	mypy pyteal tests

flake8:
	flake8 pyteal tests

lint: black mypy flake8

test-unit:
	pytest pyteal tests/unit

build-and-test: build lint test-unit

integration-test:
	pytest tests/integration

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal

.PHONY: build docs