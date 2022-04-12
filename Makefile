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

A = 3
P = 13
Q = 13
M = 10
N = 10
DEMO_PROCS=auto
graviton-demo-run:
	A=$(A) P=$(P) Q=$(Q) M=$(M) N=$(N) pytest -sv -n $(DEMO_PROCS) --durations=10 tests/demo/logicsigs_test.py::test_many_factorizer_games

# set NUM_PROCS = auto when the following issue has been fixed https://github.com/algorand/pyteal/issues/199
NUM_PROCS = 1 
integration-setup: pip-integration build
	black --check tests $(ALLPY)
	flake8 tests $(ALLPY)
	mypy tests

integration-run:
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration

integration-test: integration-setup integration-run graviton-demo-run

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal

.PHONY: build docs demo