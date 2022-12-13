# ---- Setup ---- #

setup-development:
	pip install -e .
	pip install -r requirements.txt --upgrade

setup-docs:
	pip install -r docs/requirements.txt
	pip install doc2dash

setup-wheel:
	pip install wheel

generate-init:
	python -m scripts.generate_init

# ---- Docs and Distribution ---- #

bdist-wheel:
	python setup.py sdist bdist_wheel

bundle-docs-clean:
	rm -rf docs/pyteal.docset

bundle-docs: bundle-docs-clean
	cd docs && \
	make html SPHINXOPTS="-W --keep-going" && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

# ---- Code Quality ---- #

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples pyteal scripts tests *.py
black:
	black --check $(ALLPY)

flake8:
	flake8 $(ALLPY)

MYPY = pyteal scripts tests
mypy:
	mypy --show-error-codes $(MYPY)

lint: black flake8 mypy

# ---- Unit Tests (no algod) ---- #

# TODO: add blackbox_test.py to multithreaded tests when following issue has been fixed https://github.com/algorand/pyteal/issues/199
NUM_PROCS = auto
test-unit:
	pytest -n $(NUM_PROCS) --durations=10 -sv pyteal tests/unit --ignore tests/unit/blackbox_test.py --ignore tests/unit/user_guide_test.py
	pytest -n 1 -sv tests/unit/blackbox_test.py tests/unit/user_guide_test.py

lint-and-test: check-generate-init lint test-unit

# ---- Integration Tests (algod required) ---- #

algod-start:
	docker compose up -d algod --wait

algod-stop:
	docker compose stop algod

integration-run:
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration -m "not serial"
	pytest --durations=10 -sv tests/integration -m serial

test-integration: integration-run

all-tests: lint-and-test test-integration

# ---- Local Github Actions Simulation via `act` ---- #
# assumes act is installed, e.g. via `brew install act`

ACT_JOB = run-integration-tests
local-gh-job:
	act -j $(ACT_JOB)

local-gh-simulate:
	act

# ---- Extras ---- #

coverage:
	pytest --cov-report html --cov=pyteal
