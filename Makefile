pip:
	pip install -e .

pip-development: pip
	pip install -e.[development]

pip-integration: pip-development
	pip install -e.[integration]

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

ALLPY = docs examples pyteal scripts *.py
black:
	black --check $(ALLPY)

flake8:
	flake8 $(ALLPY)

MYPY = pyteal scripts
mypy:
	mypy $(MYPY)

lint: black flake8 mypy

test-unit:
	pytest pyteal tests/unit

build-and-test: build lint test-unit

# set NUM_PROCS = auto when the following issue has been fixed https://github.com/algorand/pyteal/issues/199
NUM_PROCS = 1 
integration-test: pip-integration build
	black --check tests $(ALLPY)
	flake8 tests $(ALLPY)
	mypy tests
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal

.PHONY: build docs