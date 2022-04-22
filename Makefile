setup-development:
	pip install -e.[development]

setup-docs: setup-development
	pip install -r docs/requirements.txt
	pip install doc2dash

setup-wheel:
	pip install wheel

bdist-wheel:
	python setup.py sdist bdist_wheel

bundle-docs-clean:
	rm -rf docs/pyteal.docset

bundle-docs: bundle-docs-clean
	cd docs && \
	make html && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

generate-init:
	python -m scripts.generate_init

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples pyteal scripts tests *.py
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

sandbox-dev-up:
	docker-compose up -d algod

sandbox-dev-stop:
	docker-compose stop algod

build-and-test: check-generate-init lint test-unit

# set NUM_PROCS = auto when the following issue has been fixed https://github.com/algorand/pyteal/issues/199
NUM_PROCS = 1 
integration-run:
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration

integration-test: integration-run # graviton-demo-run

all-tests: build-and-test integration-test

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal

# assumes act is installed, e.g. via `brew install act`:
local-gh-simulate:
	act

# The following depends on [Graviton PR #9](https://github.com/algorand/graviton/pull/9):
# TODO: Delete the below before merging:
# A = 3
# P = 13
# Q = 13
# M = 10
# N = 10
# DEMO_PROCS=auto
# graviton-demo-run:
# 	A=$(A) P=$(P) Q=$(Q) M=$(M) N=$(N) pytest -sv -n $(DEMO_PROCS) --durations=10 tests/demo/logicsigs_test.py::test_many_factorizer_games
